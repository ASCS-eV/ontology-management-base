#!/usr/bin/env python3
"""
Graph Loader - RDF Graph Loading Utilities

FEATURE SET:
============
1. load_graph - Load single file into graph with auto-format detection
2. load_graphs - Load multiple files into combined graph
3. load_jsonld_files - Load JSON-LD files with prefix extraction
4. load_turtle_files - Load Turtle files into graph
5. load_jsonld_with_context - Load JSON-LD with prefix extraction
6. load_fixtures_for_iris - Resolve and load fixture files for referenced IRIs
7. extract_external_iris - Find referenced IRIs that should be fixture-loaded

FIXTURE/DID RESOLUTION:
=======================
load_fixtures_for_iris implements a catalog-first resolution strategy:

1. Catalog Resolution (Local)
   - Resolves IRIs via RegistryResolver's fixtures catalog
   - Includes DID documents registered via register_did_documents()
   - Fast, offline, deterministic

2. Online Fallback (Optional)
   - For did:web, http://, and https:// IRIs not found in catalog
   - Logs warning but continues validation
   - Enabled by default in the validation pipeline
   - Disable via --offline when fully local-only behavior is required

3. Graceful Handling
   - Unresolved IRIs are collected and returned
   - Warnings logged but validation continues
   - Caller decides how to handle unresolved references

USAGE:
======
    from src.tools.utils.graph_loader import (
        load_graph,
        load_jsonld_files,
        load_fixtures_for_iris,
    )

    # Load single file
    graph = load_graph(Path("data/instance.json"))

    # Load multiple JSON-LD files
    graph, prefixes = load_jsonld_files(json_files, root_dir)

    # Resolve external references (e.g., did:web: IRIs or locally mapped fixtures)
    external_iris = extract_external_iris(graph)
    loaded, unresolved = load_fixtures_for_iris(
        external_iris, resolver, graph, root_dir
    )

STANDALONE TESTING:
==================
    python3 -m src.tools.utils.graph_loader [--test] [--verbose] [files...]

DEPENDENCIES:
=============
- rdflib: For RDF graph handling
- oxrdflib (optional): For Oxigraph performance optimization

NOTES:
======
- FAST_STORE is imported from core.constants
- This module consolidates all graph loading logic
- All other modules should delegate graph loading here
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.request import Request, build_opener, HTTPSHandler

import rdflib
from rdflib import Graph

from src.tools.core.constants import FAST_STORE
from src.tools.core.iri_utils import did_web_to_url, is_did_web
from src.tools.core.logging import get_logger
from src.tools.utils.print_formatter import normalize_path_for_display

# Module logger
logger = get_logger(__name__)

# Re-export FAST_STORE for backwards compatibility
__all__ = [
    "FAST_STORE",
    "load_graph",
    "load_graphs",
    "load_jsonld_files",
    "load_turtle_files",
    "load_jsonld_with_context",
    "load_fixtures_for_iris",
    "extract_external_iris",
]


def load_graph(
    file_path: Path,
    format: str = "auto",
    store: str = None,
) -> Graph:
    """
    Load single file into graph with auto-format detection.

    Args:
        file_path: Path to the file to load
        format: RDF format ("auto", "json-ld", "turtle", etc.)
        store: RDF store to use (default: auto-detect oxigraph)

    Returns:
        Graph containing the loaded triples
    """
    if store is None:
        store = FAST_STORE

    graph = Graph(store=store)
    path = Path(file_path)

    # Auto-detect format from extension
    if format == "auto":
        suffix = path.suffix.lower()
        if suffix in (".json", ".jsonld"):
            format = "json-ld"
        elif suffix == ".ttl":
            format = "turtle"
        elif suffix in (".rdf", ".xml"):
            format = "xml"
        elif suffix == ".nt":
            format = "nt"
        else:
            format = "turtle"  # Default fallback

    graph.parse(str(path), format=format)
    return graph


def load_graphs(
    file_paths: List[Path],
    format: str = "auto",
    store: str = None,
) -> Graph:
    """
    Load multiple files into a combined graph.

    Args:
        file_paths: List of file paths to load
        format: RDF format ("auto" for auto-detection)
        store: RDF store to use

    Returns:
        Graph containing all loaded triples
    """
    if store is None:
        store = FAST_STORE

    combined = Graph(store=store)

    for path in file_paths:
        if not path.exists():
            logger.error("Graph file not found: %s", path)
            raise FileNotFoundError(f"Graph file not found: {path}")
        try:
            temp_graph = load_graph(path, format=format, store="default")
            combined += temp_graph
        except Exception as e:
            logger.error("Failed to load %s: %s", path, e)
            raise RuntimeError(f"Failed to load graph file {path}: {e}") from e

    return combined


def load_jsonld_files(
    files: List[Path],
    root_dir: Path,
    store: str = None,
    context_url_map: Optional[Dict[str, Path]] = None,
) -> Tuple[Graph, Dict[str, str]]:
    """
    Load JSON-LD files into a graph with prefix extraction.

    When ``context_url_map`` is provided, remote ``@context`` URLs that
    match entries in the map are inlined from local files before parsing.
    This avoids network fetches for unpublished or unreachable contexts.

    Args:
        files: List of JSON-LD file paths to load
        root_dir: Repository root directory for path normalization
        store: RDF store to use (default: auto-detect oxigraph)
        context_url_map: Optional mapping of context URL → local file path.
            When provided, contexts are inlined before rdflib parsing.

    Returns:
        Tuple of (graph, prefixes) where prefixes is a dict of prefix->namespace
    """
    if store is None:
        store = FAST_STORE

    graph = Graph(store=store)
    prefixes: Dict[str, str] = {}

    for json_file in files:
        rel_path = normalize_path_for_display(json_file, root_dir)

        # Extract prefixes from @context
        try:
            file_prefixes = _extract_prefixes_from_jsonld(json_file)
            prefixes.update(file_prefixes)
        except Exception as e:
            logger.debug("Could not extract prefixes from %s: %s", rel_path, e)

        # Parse into graph, with optional context inlining
        try:
            if context_url_map:
                from src.tools.utils.context_resolver import (
                    load_jsonld_with_local_contexts,
                )

                json_str = load_jsonld_with_local_contexts(json_file, context_url_map)
                graph.parse(
                    data=json_str,
                    format="json-ld",
                    base=json_file.resolve().as_uri(),
                    publicID=json_file.resolve().as_uri(),
                )
            else:
                graph.parse(str(json_file), format="json-ld")
        except Exception as e:
            logger.error("Failed to load %s: %s", rel_path, e)
            err_str = str(e)
            if "HTTP Error" in err_str or "urlopen error" in err_str:
                raise RuntimeError(
                    f"Failed to load {rel_path}: could not fetch remote @context URL.\n"
                    f"  Cause: {e}\n"
                    f"  Hint: Ensure all @context URLs are mapped to local files via "
                    f"--artifacts, or check that the URL is published and reachable."
                ) from e
            if "Invalid IRI" in err_str or isinstance(e, ValueError):
                raise RuntimeError(
                    f"Failed to load {rel_path}: invalid IRI encountered during "
                    f"JSON-LD parsing.\n"
                    f"  Cause: {e}\n"
                    f"  Hint: Check that all @context URLs are mapped to local files "
                    f"via --artifacts. A missing context mapping can cause bare terms "
                    f"to produce invalid IRIs."
                ) from e
            raise

    return graph, prefixes


def load_turtle_files(
    files: List[Path],
    root_dir: Path,
    store: str = None,
) -> Graph:
    """
    Load Turtle files into a graph.

    Args:
        files: List of Turtle file paths to load
        root_dir: Repository root directory for path normalization
        store: RDF store to use (default: auto-detect oxigraph)

    Returns:
        Graph containing all loaded triples
    """
    if store is None:
        store = FAST_STORE

    graph = Graph(store=store)

    for ttl_file in files:
        rel_path = normalize_path_for_display(ttl_file, root_dir)

        if not ttl_file.exists():
            logger.error("Turtle file not found: %s", rel_path)
            raise FileNotFoundError(f"Turtle file not found: {rel_path}")

        try:
            graph.parse(str(ttl_file), format="turtle")
        except Exception as e:
            logger.error("Failed to load %s: %s", rel_path, e)
            raise RuntimeError(f"Failed to load {rel_path}: {e}") from e

    return graph


def load_jsonld_with_context(file_path: Path) -> Tuple[Graph, Dict[str, str]]:
    """
    Load JSON-LD file with prefix extraction.

    Args:
        file_path: Path to JSON-LD file

    Returns:
        Tuple of (graph, prefixes) where prefixes is dict of prefix->namespace
    """
    graph = Graph(store=FAST_STORE)
    graph.parse(str(file_path), format="json-ld")

    prefixes = _extract_prefixes_from_jsonld(file_path)

    return graph, prefixes


def _load_online_did_web_document(
    iri: str,
    graph: Graph,
    context_url_map: Optional[Dict[str, Path]] = None,
) -> str:
    """Fetch and load a did:web document into the graph."""
    requested_did = re.split(r"[/?#]", iri, maxsplit=1)[0]
    document_url = did_web_to_url(iri)
    if not document_url:
        raise ValueError(f"Not a did:web identifier: {iri}")

    request = Request(
        document_url,
        headers={
            "Accept": (
                "application/did+ld+json, application/did+json, "
                "application/ld+json, application/json"
            )
        },
    )

    # Use a custom opener that does NOT follow redirects to prevent SSRF
    # via attacker-controlled 3xx responses targeting internal services.
    _no_redirect_opener = build_opener(HTTPSHandler)

    with _no_redirect_opener.open(request, timeout=10) as response:
        payload = response.read().decode("utf-8")

    did_document = json.loads(payload)
    if not isinstance(did_document, dict):
        raise ValueError(f"Resolved did:web document is not a JSON object: {iri}")
    if did_document.get("id") != requested_did:
        raise ValueError(
            f"Resolved did:web document id mismatch for {iri}: {did_document.get('id')}"
        )
    if context_url_map:
        from src.tools.utils.context_resolver import inline_jsonld_with_local_contexts

        json_str = inline_jsonld_with_local_contexts(
            did_document,
            context_url_map,
            source_name=document_url,
        )
    else:
        json_str = json.dumps(did_document)

    did_graph = Graph(store=FAST_STORE)
    did_graph.parse(
        data=json_str,
        format="json-ld",
        base=document_url,
        publicID=document_url,
    )
    if len(did_graph) == 0:
        raise ValueError(
            f"Resolved did:web document produced no RDF triples for {iri}; "
            "plain DID JSON without JSON-LD context is not supported by OMB graph loading"
        )
    graph += did_graph
    return document_url


def load_fixtures_for_iris(
    iris: Set[str],
    resolver: "RegistryResolver",  # noqa: F821 - forward reference
    graph: Graph,
    root_dir: Path,
    context_url_map: Optional[Dict[str, Path]] = None,
    allow_online_fallback: bool = True,
    verbose: bool = False,
) -> Tuple[int, List[str]]:
    """
    Load fixture files for external IRI references.

    Resolution strategy (catalog-first):
    1. Try to resolve via catalog (local fixtures)
    2. If not found and allow_online_fallback=True, attempt online resolution
    3. Log warning for unresolved IRIs (not an error)

    Args:
        iris: Set of IRIs to resolve
        resolver: RegistryResolver instance
        graph: Graph to load fixtures into
        root_dir: Repository root directory
        context_url_map: Optional mapping of context URL → local file path.
            When provided, fixture JSON-LD is loaded with the same local
            context inlining used for top-level data files.
        allow_online_fallback: If True, attempt online resolution for
            unresolved IRIs, including ``did:web`` documents. Default True.
        verbose: If True, print details about each resolved fixture.

    Returns:
        Tuple of (fixtures_loaded_count, list_of_unresolved_iris)
    """
    fixtures_loaded = 0
    unresolved_iris: List[str] = []
    existing_subjects = {str(s) for s in graph.subjects()}

    for iri in sorted(iris):
        # Skip if already in graph
        if iri in existing_subjects:
            if verbose:
                print(f"    ✓ Already in graph: {iri}")
            continue

        # Step 1: Try to resolve via catalog (local fixtures)
        fixture_path = resolver.resolve_fixture_iri(iri)
        if fixture_path:
            abs_path = resolver.to_absolute(fixture_path)
            if abs_path.exists():
                try:
                    if context_url_map:
                        from src.tools.utils.context_resolver import (
                            load_jsonld_with_local_contexts,
                        )

                        json_str = load_jsonld_with_local_contexts(
                            abs_path, context_url_map
                        )
                        graph.parse(data=json_str, format="json-ld")
                    else:
                        graph.parse(str(abs_path), format="json-ld")
                    rel_path = normalize_path_for_display(abs_path, root_dir)
                    logger.debug("Loaded fixture: %s for %s", rel_path, iri)
                    if verbose:
                        print(f"    ✓ Loaded fixture: {rel_path}")
                    fixtures_loaded += 1
                    continue
                except Exception as e:
                    logger.warning("Could not load fixture for %s: %s", iri, e)

        # Step 2: Try online did:web resolution if enabled
        if allow_online_fallback and is_did_web(iri):
            try:
                document_url = _load_online_did_web_document(
                    iri,
                    graph,
                    context_url_map=context_url_map,
                )
                logger.info("Resolved did:web online: %s via %s", iri, document_url)
                if verbose:
                    print(f"    ⚡ Resolved did:web: {iri} -> {document_url}")
                fixtures_loaded += 1
                continue
            except Exception as e:
                logger.warning("Could not resolve did:web %s online: %s", iri, e)

        # Step 3: Try online HTTP(S) resolution if enabled
        if allow_online_fallback and iri.startswith(("http://", "https://")):
            try:
                graph.parse(iri, format="json-ld")
                logger.info("Resolved online: %s", iri)
                if verbose:
                    print(f"    ⚡ Resolved online: {iri}")
                fixtures_loaded += 1
                continue
            except Exception as e:
                logger.warning("Could not resolve online %s: %s", iri, e)

        # Step 4: Mark as unresolved (warning, not error)
        unresolved_iris.append(iri)
        logger.warning("Unresolved IRI (continuing validation): %s", iri)

    return fixtures_loaded, unresolved_iris


def _extract_prefixes_from_jsonld(file_path: Path) -> Dict[str, str]:
    """
    Extract prefix mappings from a JSON-LD @context.

    Args:
        file_path: Path to JSON-LD file

    Returns:
        Dictionary of prefix -> namespace URI mappings
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    context = data.get("@context", {})
    prefixes = {}

    if isinstance(context, dict):
        for key, value in context.items():
            if isinstance(value, str) and (value.endswith("#") or value.endswith("/")):
                prefixes[key] = value
    elif isinstance(context, list):
        for ctx in context:
            if isinstance(ctx, dict):
                for key, value in ctx.items():
                    if isinstance(value, str) and (
                        value.endswith("#") or value.endswith("/")
                    ):
                        prefixes[key] = value

    return prefixes


def extract_external_iris(
    graph: Graph,
    resolver: Optional["RegistryResolver"] = None,  # noqa: F821 - forward reference
) -> Set[str]:
    """
    Extract referenced IRIs that should trigger fixture loading.

    By default this preserves the historical behaviour of collecting
    ``did:web:`` IRIs. When a ``resolver`` is provided, the function also
    collects any URIRef that resolves to a locally registered fixture path.
    This allows validation to load referenced local data such as ``did:ethr``
    documents or other fixture resources whose identifiers are present in the
    data graph.

    Args:
        graph: RDF graph to scan
        resolver: Optional registry resolver used to detect locally resolvable
            fixture IRIs beyond ``did:web:``.

    Returns:
        Set of referenced IRIs eligible for fixture loading
    """
    external_iris = set()

    for s, p, o in graph:
        if isinstance(s, rdflib.URIRef):
            subj = str(s)
            if is_did_web(subj) or (resolver and resolver.resolve_fixture_iri(subj)):
                external_iris.add(subj)
        if isinstance(o, rdflib.URIRef):
            obj = str(o)
            if is_did_web(obj) or (resolver and resolver.resolve_fixture_iri(obj)):
                external_iris.add(obj)

    return external_iris


def _run_tests() -> bool:
    """Run self-tests for the module."""
    import tempfile

    print("Running graph_loader self-tests...")
    all_passed = True

    # Test 1: FAST_STORE is defined
    if FAST_STORE not in ("oxigraph", "default"):
        print(f"FAIL: Invalid FAST_STORE value: {FAST_STORE}")
        all_passed = False
    else:
        print(f"PASS: FAST_STORE is '{FAST_STORE}'")

    # Test 2: Create and load JSON-LD file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test JSON-LD file
        jsonld_file = tmppath / "test.json"
        jsonld_content = {
            "@context": {"@vocab": "http://example.org/"},
            "@id": "http://example.org/test",
            "@type": "Thing",
        }
        jsonld_file.write_text(json.dumps(jsonld_content))

        # Test load_graph
        try:
            graph = load_graph(jsonld_file)
            if len(graph) < 1:
                print("FAIL: Graph should have at least 1 triple")
                all_passed = False
            else:
                print("PASS: load_graph JSON-LD")
        except Exception as e:
            print(f"FAIL: load_graph raised exception: {e}")
            all_passed = False

        # Test load_jsonld_files
        try:
            graph, prefixes = load_jsonld_files([jsonld_file], tmppath)
            if len(graph) < 1:
                print("FAIL: load_jsonld_files should have triples")
                all_passed = False
            else:
                print("PASS: load_jsonld_files")
        except Exception as e:
            print(f"FAIL: load_jsonld_files raised exception: {e}")
            all_passed = False

        # Create test Turtle file
        ttl_file = tmppath / "test.ttl"
        ttl_content = """@prefix ex: <http://example.org/> .
ex:subject a ex:Thing .
"""
        ttl_file.write_text(ttl_content)

        # Test load_turtle_files
        try:
            graph = load_turtle_files([ttl_file], tmppath)
            if len(graph) < 1:
                print("FAIL: load_turtle_files should have triples")
                all_passed = False
            else:
                print("PASS: load_turtle_files")
        except Exception as e:
            print(f"FAIL: load_turtle_files raised exception: {e}")
            all_passed = False

        # Test extract_external_iris
        external_graph = Graph()
        external_graph.parse(
            data="""
            @prefix ex: <http://example.org/> .
            <did:web:test.example:subject> a ex:Thing .
            ex:other ex:ref <did:web:test.example:ref> .
            """,
            format="turtle",
        )
        iris = extract_external_iris(external_graph)
        if len(iris) != 2:
            print(f"FAIL: Expected 2 external IRIs, got {len(iris)}")
            all_passed = False
        else:
            print("PASS: extract_external_iris")

    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")

    return all_passed


def main():
    """CLI entry point for graph_loader."""
    parser = argparse.ArgumentParser(description="Load and inspect RDF graphs")
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to load",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--format",
        "-f",
        default="auto",
        help="RDF format (auto, json-ld, turtle, etc.)",
    )

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    if not args.files:
        parser.print_help()
        sys.exit(1)

    # Load and report
    root_dir = Path.cwd()
    total_triples = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            graph = load_graph(path, format=args.format)
            triple_count = len(graph)
            total_triples += triple_count

            rel_path = normalize_path_for_display(path, root_dir)
            print(f"{rel_path}: {triple_count} triples")

            if args.verbose:
                for s, p, o in list(graph)[:5]:
                    print(f"  {s} {p} {o}")
                if len(graph) > 5:
                    print(f"  ... and {len(graph) - 5} more")

        except Exception as e:
            display_path = str(file_path).replace("\\", "/")
            print(f"Error loading {display_path}: {e}", file=sys.stderr)

    print(f"\nTotal: {total_triples} triples from {len(args.files)} file(s)")


if __name__ == "__main__":
    main()
