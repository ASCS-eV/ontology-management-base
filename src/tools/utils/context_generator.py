#!/usr/bin/env python3
"""
JSON-LD Context Generator - Generates context files from OWL/SHACL artifacts.

This script parses OWL ontologies and SHACL shapes to generate JSON-LD context
files that enable compact JSON-LD instance syntax. It extracts datatype
information from SHACL property constraints and maps them to JSON-LD type
coercion rules.

FEATURE SET:
============
1. generate_context - Generate JSON-LD context from OWL+SHACL for a domain
2. generate_all_contexts - Generate contexts for all domains in artifacts/
3. extract_property_datatypes - Extract datatypes from SHACL shapes
4. test_context_roundtrip - Verify context produces equivalent RDF triples

USAGE:
======
    # Generate context for a specific domain
    python -m src.tools.utils.context_generator --domain manifest

    # Generate contexts for all domains
    python -m src.tools.utils.context_generator --all

    # Test round-trip equivalence
    python -m src.tools.utils.context_generator --test-roundtrip manifest

STANDALONE TESTING:
==================
    python -m src.tools.utils.context_generator --test

DEPENDENCIES:
=============
- rdflib: RDF graph parsing and manipulation

NOTES:
======
- This is a transitional tool bridging to full LinkML adoption
- Context files enable compact JSON-LD syntax without explicit @value/@type
- The generator extracts datatypes from sh:datatype, sh:class, sh:nodeKind
"""

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rdflib import RDF, Graph, Namespace, URIRef
from rdflib.namespace import OWL, XSD

from src.tools.core.constants import FAST_STORE, Extensions
from src.tools.core.iri_utils import get_local_name, normalize_iri
from src.tools.core.logging import get_logger
from src.tools.utils.graph_loader import load_graph, load_graphs
from src.tools.utils.print_formatter import normalize_path_for_display

logger = get_logger(__name__)

# Constants
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
LINKML_DIR = ROOT_DIR / "linkml"

# Namespaces
SH = Namespace("http://www.w3.org/ns/shacl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
SCHEMA = Namespace("https://schema.org/")

# XSD datatype mappings for JSON-LD context
XSD_TYPE_MAP = {
    str(XSD.string): None,  # Default, no coercion needed
    str(XSD.integer): "xsd:integer",
    str(XSD.int): "xsd:int",
    str(XSD.float): "xsd:float",
    str(XSD.double): "xsd:double",
    str(XSD.decimal): "xsd:decimal",
    str(XSD.boolean): "xsd:boolean",
    str(XSD.date): "xsd:date",
    str(XSD.dateTime): "xsd:dateTime",
    str(XSD.time): "xsd:time",
    str(XSD.anyURI): "xsd:anyURI",
    str(XSD.nonNegativeInteger): "xsd:nonNegativeInteger",
    str(XSD.positiveInteger): "xsd:positiveInteger",
}


from src.tools.utils.file_collector import write_if_changed  # noqa: E402


def extract_ontology_iri(owl_graph: Graph) -> Optional[str]:
    """Extract the ontology IRI from an OWL graph."""
    for s in owl_graph.subjects(RDF.type, OWL.Ontology):
        return str(s)
    return None


def _build_ns_prefix_lookup(graph: Graph) -> Dict[str, str]:
    """Build a reverse lookup from namespace URI to declared prefix name.

    Uses the ``@prefix`` declarations from the parsed Turtle source
    (available via ``graph.namespaces()``).  This is the
    standards-conformant way to resolve prefix names — the ontology
    author's declared prefixes are authoritative.

    Returns:
        Dict mapping namespace URI strings to prefix name strings.
    """
    lookup: Dict[str, str] = {}
    for prefix, ns in graph.namespaces():
        prefix_str = str(prefix)
        ns_str = str(ns)
        if prefix_str:
            lookup[ns_str] = prefix_str
    return lookup


def _lookup_prefix(ns_lookup: Dict[str, str], iri: str) -> Optional[str]:
    """Look up a prefix for an IRI using declared namespace bindings.

    Tries the normalized IRI (with trailing ``/``) and both ``/`` and
    ``#`` variants to handle hash-vs-slash namespace mismatches.

    Args:
        ns_lookup: Mapping from namespace URI to prefix name
            (built by :func:`_build_ns_prefix_lookup`).
        iri: The ontology IRI to look up.

    Returns:
        The declared prefix name, or ``None`` if not found.
    """
    normalized = normalize_iri(iri, trailing_slash=True)
    if normalized in ns_lookup:
        return ns_lookup[normalized]

    base = iri.rstrip("/#")
    for variant in (base + "#", base + "/"):
        if variant in ns_lookup:
            return ns_lookup[variant]

    return None


def _walk_rdf_list(graph: Graph, list_head):
    """Yield each item from an RDF list (rdf:first / rdf:rest chain)."""
    current = list_head
    while current and current != RDF.nil:
        item = graph.value(current, RDF.first)
        if item:
            yield item
        current = graph.value(current, RDF.rest)


def _analyze_or_branches(
    shacl_graph: Graph, prop_node: URIRef
) -> tuple[Optional[str], bool]:
    """Analyze sh:or branches and return (literal_datatype, has_object_branch).

    For polymorphic SHACL properties using sh:or, this inspects each branch to
    determine whether it constrains a literal datatype, an object reference, or
    both.  Returns the first literal datatype found (as a full IRI string) and
    whether any object-type branch exists.
    """
    or_list = shacl_graph.value(prop_node, SH["or"])
    if or_list is None:
        return None, False

    literal_datatype: Optional[str] = None
    has_object = False

    for item in _walk_rdf_list(shacl_graph, or_list):
        # Check for literal datatype branch
        dt = shacl_graph.value(item, SH.datatype)
        if dt is not None and literal_datatype is None:
            literal_datatype = str(dt)
            continue

        # Check for object branch (sh:node, sh:class, sh:nodeKind IRI)
        if shacl_graph.value(item, SH.node) is not None:
            has_object = True
        elif shacl_graph.value(item, SH["class"]) is not None:
            has_object = True
        elif shacl_graph.value(item, SH.nodeKind) == SH.IRI:
            has_object = True
        else:
            # Check sh:and branches inside sh:or
            and_list = shacl_graph.value(item, SH["and"])
            if and_list is not None:
                for and_item in _walk_rdf_list(shacl_graph, and_list):
                    if shacl_graph.value(and_item, SH.node) is not None:
                        has_object = True
                        break
                    if shacl_graph.value(and_item, SH["class"]) is not None:
                        has_object = True
                        break

    return literal_datatype, has_object


def extract_property_datatypes(
    shacl_graph: Graph, domain_prefix: str, domain_iri: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract property definitions and datatypes from SHACL shapes.

    Returns a dict mapping property local names to their context definitions:
    {
        "filePath": {"@id": "manifest:filePath", "@type": "xsd:anyURI"},
        "mimeType": {"@id": "manifest:mimeType"},
        "hasFileMetadata": {"@id": "manifest:hasFileMetadata", "@type": "@id"},
    }
    """
    properties: Dict[str, Dict[str, Any]] = {}

    # Find all property constraints in SHACL shapes
    for shape in shacl_graph.subjects(RDF.type, SH.NodeShape):
        # Get properties defined on this shape
        for prop_node in shacl_graph.objects(shape, SH.property):
            path = shacl_graph.value(prop_node, SH.path)
            if not path:
                continue

            path_str = str(path)

            # Only process properties from this domain
            if not path_str.startswith(domain_iri):
                # Also handle external properties we want to map
                # (skos:note, sh:conformsTo)
                # NOTE: schema: properties (name, description) are NOT mapped
                # here — they come from the gx context. Duplicating them in
                # domain contexts would override domain-specific terms with
                # the same local name (e.g. service:description).
                if path_str.startswith(str(SKOS)):
                    local_name = path_str.replace(str(SKOS), "")
                    properties[local_name] = {"@id": f"skos:{local_name}"}
                elif path_str.startswith(str(SH)):
                    local_name = path_str.replace(str(SH), "")
                    if local_name == "conformsTo":
                        properties[local_name] = {
                            "@id": "sh:conformsTo",
                            "@type": "@id",
                            "@container": "@set",
                        }
                continue

            # Extract local name using namespace-aware splitting
            domain_ns = normalize_iri(domain_iri, trailing_slash=True)
            if path_str.startswith(domain_ns):
                local_name = path_str[len(domain_ns) :]
            else:
                local_name = get_local_name(path_str)

            # Determine the type coercion
            datatype = shacl_graph.value(prop_node, SH.datatype)
            node_kind = shacl_graph.value(prop_node, SH.nodeKind)
            node_ref = shacl_graph.value(prop_node, SH.node)
            class_ref = shacl_graph.value(prop_node, SH["class"])

            prop_def: Dict[str, Any] = {"@id": f"{domain_prefix}:{local_name}"}

            if datatype:
                datatype_str = str(datatype)
                if datatype_str in XSD_TYPE_MAP:
                    mapped_type = XSD_TYPE_MAP[datatype_str]
                    if mapped_type:
                        prop_def["@type"] = mapped_type
                else:
                    # Unknown datatype, preserve it
                    prop_def["@type"] = datatype_str

            elif node_kind == SH.IRI or class_ref or node_ref:
                # Object property - reference to another node
                prop_def["@type"] = "@id"

            else:
                # Polymorphic: sh:or may mix literal datatypes and object refs.
                # Prefer the literal datatype so JSON-LD coercion produces
                # typed literals; object branches still work via explicit
                # {"@type": "ClassName"} syntax in instance data.
                or_datatype, has_object_branch = _analyze_or_branches(
                    shacl_graph, prop_node
                )
                if or_datatype:
                    if or_datatype in XSD_TYPE_MAP:
                        mapped = XSD_TYPE_MAP[or_datatype]
                        if mapped:
                            prop_def["@type"] = mapped
                    else:
                        prop_def["@type"] = or_datatype
                elif has_object_branch:
                    prop_def["@type"] = "@id"

            # Deterministic conflict resolution: when the same property appears
            # in multiple SHACL shapes with different datatypes, pick the
            # safest coercion.  "No @type" means the shape declared
            # xsd:string (or had no type info) — that is a legitimate type
            # signal, not merely "unknown".
            if local_name in properties:
                existing = properties[local_name]
                if existing != prop_def:
                    existing_type = existing.get("@type")
                    new_type = prop_def.get("@type")

                    if existing_type == new_type:
                        pass  # identical coercion — keep existing

                    elif existing_type == "@id" and not new_type:
                        # Object ref vs. plain literal — drop @id so plain
                        # string values are not coerced into IRIs.
                        logger.warning(
                            "Property '%s': conflicting @id vs untyped — "
                            "dropping coercion",
                            local_name,
                        )
                        properties[local_name] = prop_def  # no @type

                    elif not existing_type and new_type == "@id":
                        pass  # keep existing (no coercion is safer)

                    elif existing_type == "@id" and new_type and new_type != "@id":
                        # Object ref vs. concrete literal — prefer literal.
                        logger.warning(
                            "Property '%s': conflicting @id vs %s — using literal type",
                            local_name,
                            new_type,
                        )
                        properties[local_name] = prop_def

                    elif new_type == "@id" and existing_type and existing_type != "@id":
                        pass  # keep existing literal type

                    elif (existing_type and not new_type) or (
                        not existing_type and new_type
                    ):
                        # One shape typed, the other string/default — drop
                        # coercion so both variants can pass through.
                        logger.warning(
                            "Property '%s' has conflicting datatypes: "
                            "%s vs %s — dropping coercion",
                            local_name,
                            existing_type or "(string)",
                            new_type or "(string)",
                        )
                        properties[local_name] = {
                            k: v for k, v in existing.items() if k != "@type"
                        }

                    elif existing_type and new_type and existing_type != new_type:
                        # Two different literal types — drop coercion to
                        # avoid forcing a wrong cast on either shape.
                        logger.warning(
                            "Property '%s' has conflicting datatypes: "
                            "%s vs %s — dropping coercion",
                            local_name,
                            existing_type,
                            new_type,
                        )
                        properties[local_name] = {
                            k: v for k, v in existing.items() if k != "@type"
                        }
            else:
                properties[local_name] = prop_def

    return properties


def extract_classes(owl_graph: Graph, domain_iri: str) -> Set[str]:
    """Extract class local names from the OWL ontology."""
    classes = set()
    domain_ns = normalize_iri(domain_iri, trailing_slash=True)

    for cls in owl_graph.subjects(RDF.type, OWL.Class):
        cls_str = str(cls)
        if cls_str.startswith(domain_ns):
            local_name = cls_str[len(domain_ns) :]
            if local_name and "/" not in local_name:
                classes.add(local_name)
        elif cls_str.startswith(domain_iri) and not cls_str.startswith("http", 1):
            local_name = get_local_name(cls_str)
            if local_name:
                classes.add(local_name)

    return classes


def generate_context(domain: str) -> Optional[Dict[str, Any]]:
    """
    Generate a JSON-LD context for a domain.

    Args:
        domain: Domain name (e.g., 'manifest', 'hdmap')

    Returns:
        JSON-LD context dictionary, or None if generation fails
    """
    domain_dir = ARTIFACTS_DIR / domain
    owl_path = domain_dir / f"{domain}{Extensions.OWL}"
    shacl_path = domain_dir / f"{domain}{Extensions.SHACL}"

    if not owl_path.exists():
        logger.error(
            "OWL file not found: %s",
            normalize_path_for_display(owl_path, ROOT_DIR),
        )
        return None

    # Handle domains with multiple SHACL files or non-standard naming
    shacl_paths: List[Path] = []
    if shacl_path.exists():
        shacl_paths.append(shacl_path)
    else:
        # Look for any .shacl.ttl files in the domain directory
        shacl_paths = sorted(domain_dir.glob(f"*{Extensions.SHACL}"))
        if not shacl_paths:
            logger.error(
                "No SHACL files found in: %s",
                normalize_path_for_display(domain_dir, ROOT_DIR),
            )
            return None
        logger.info(
            "Using %d SHACL file(s) for domain '%s': %s",
            len(shacl_paths),
            domain,
            [p.name for p in shacl_paths],
        )

    # Parse OWL graph
    owl_graph = load_graph(owl_path, format="turtle")

    # Parse and merge all SHACL graphs
    shacl_graph = load_graphs(shacl_paths, format="turtle")

    if len(shacl_graph) == 0:
        logger.error("Failed to parse any SHACL files for domain '%s'", domain)
        return None

    # Extract ontology IRI
    ontology_iri = extract_ontology_iri(owl_graph)
    if not ontology_iri:
        logger.error(
            "Could not extract ontology IRI from %s",
            normalize_path_for_display(owl_path, ROOT_DIR),
        )
        return None

    logger.info("Processing domain '%s' with IRI: %s", domain, ontology_iri)

    # Build reverse lookup from namespace URIs to author-declared prefix names.
    # This uses the @prefix declarations from the Turtle source, which are the
    # authoritative prefix-to-namespace mappings.
    ns_lookup = _build_ns_prefix_lookup(owl_graph)

    # Determine prefix from namespace bindings, fall back to domain name
    prefix = _lookup_prefix(ns_lookup, ontology_iri) or domain

    # Build context
    context: Dict[str, Any] = {
        # JSON-LD 1.1 required for @container features
        "@version": 1.1,
        # Standard prefixes
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "sh": "http://www.w3.org/ns/shacl#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "schema": "https://schema.org/",
        # Domain prefix
        prefix: normalize_iri(ontology_iri, trailing_slash=True),
    }

    # Reserved keys that properties/classes must not overwrite
    reserved_keys = set(context.keys())

    # Add prefixes for imported ontologies resolved from owl:imports IRIs.
    # Only uses author-declared @prefix bindings; imports without a matching
    # declaration are skipped with a warning (no heuristic guessing).
    for imported in sorted(owl_graph.objects(URIRef(ontology_iri), OWL.imports)):
        imported_str = str(imported)
        imported_prefix = _lookup_prefix(ns_lookup, imported_str)
        if not imported_prefix:
            logger.warning(
                "No @prefix declaration for <%s> in %s, skipping import prefix",
                imported_str,
                domain,
            )
            continue
        if imported_prefix not in context:
            imported_ns = normalize_iri(imported_str, trailing_slash=True)
            context[imported_prefix] = imported_ns
            reserved_keys.add(imported_prefix)

    # Extract property definitions from SHACL
    properties = extract_property_datatypes(shacl_graph, prefix, ontology_iri)

    # Add properties to context, warning on collisions
    for key, value in sorted(properties.items()):
        if key in reserved_keys:
            logger.warning(
                "Property '%s' collides with reserved prefix in domain '%s', skipping",
                key,
                domain,
            )
            continue
        context[key] = value

    # Extract and add class term mappings for compact @type usage
    # This allows: "@type": "Manifest" instead of "@type": "manifest:Manifest"
    classes = extract_classes(owl_graph, ontology_iri)
    for class_name in sorted(classes):
        if class_name in reserved_keys:
            logger.warning(
                "Class '%s' collides with reserved prefix in domain '%s', skipping",
                class_name,
                domain,
            )
            continue
        # Map bare class names to full IRIs for @type expansion
        context[class_name] = f"{prefix}:{class_name}"

    # Build source_shacl value (single path or list)
    if len(shacl_paths) == 1:
        source_shacl = shacl_paths[0].relative_to(ROOT_DIR).as_posix()
    else:
        source_shacl = [p.relative_to(ROOT_DIR).as_posix() for p in shacl_paths]

    # Build the full context document
    context_doc = {
        "comments": {
            "description": "Auto-generated JSON-LD context for compact instance syntax",
            "generator": "context_generator.py",
            "source_owl": owl_path.relative_to(ROOT_DIR).as_posix(),
            "source_shacl": source_shacl,
            "note": "Transitional artifact - will be replaced by LinkML-generated context",
        },
        "@context": context,
    }

    return context_doc


def _write_context(
    domain: str, context_doc: Dict[str, Any], dry_run: bool = False
) -> Optional[Path]:
    """Write context document to file only if content has changed.

    Args:
        domain: Domain name
        context_doc: The context document to write
        dry_run: If True, do not write the file

    Returns:
        Path if file was written, None if unchanged or dry_run
    """
    output_path = ARTIFACTS_DIR / domain / f"{domain}{Extensions.CONTEXT}"
    new_content = json.dumps(context_doc, indent=3) + "\n"

    if dry_run:
        return None

    if write_if_changed(output_path, new_content):
        logger.info("Written: %s", normalize_path_for_display(output_path, ROOT_DIR))
        return output_path
    else:
        logger.debug("Context unchanged: %s", output_path.name)
        return None


def generate_all_contexts(
    exclude: Optional[List[str]] = None,
    dry_run: bool = False,
) -> Dict[str, Optional[Path]]:
    """
    Generate contexts for all domains in artifacts/.

    Args:
        exclude: List of domains to skip. Pass None to auto-detect
            LinkML-managed domains (those with a linkml/<domain>/ folder).
        dry_run: If True, generate but do not write files

    Returns:
        Dict mapping domain names to output paths (or None if
        failed/unchanged/skipped)
    """
    if exclude is None:
        # Auto-detect LinkML-managed domains (they have their own generated context)
        exclude = []
        if LINKML_DIR.is_dir():
            for d in LINKML_DIR.iterdir():
                if d.is_dir() and (d / f"{d.name}.yaml").exists():
                    exclude.append(d.name)
        # Also exclude domains whose context was generated by external LinkML
        for ctx_file in ARTIFACTS_DIR.glob("*/*.context.jsonld"):
            domain = ctx_file.parent.name
            if domain not in exclude:
                try:
                    with open(ctx_file, "r", encoding="utf-8") as f:
                        doc = json.load(f)
                    comments = doc.get("comments", {})
                    desc = comments.get("description", "")
                    if "LinkML" in desc or "linkml" in desc:
                        exclude.append(domain)
                except (json.JSONDecodeError, OSError):
                    pass
    results: Dict[str, Optional[Path]] = {}

    for domain_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not domain_dir.is_dir():
            continue

        domain = domain_dir.name
        if domain in exclude:
            logger.info("Skipping excluded domain: %s", domain)
            results[domain] = None
            continue

        owl_path = domain_dir / f"{domain}{Extensions.OWL}"
        if not owl_path.exists():
            logger.debug("No OWL file in %s, skipping", domain)
            continue

        context_doc = generate_context(domain)
        if context_doc:
            results[domain] = _write_context(domain, context_doc, dry_run=dry_run)
        else:
            results[domain] = None

    return results


def test_context_roundtrip(domain: str, instance_path: Path) -> bool:
    """
    Test that a compact instance produces equivalent RDF triples.

    This test:
    1. Loads the original verbose instance
    2. Loads a compact version using the generated context
    3. Compares the resulting RDF graphs for isomorphism

    Args:
        domain: Domain name
        instance_path: Path to a verbose JSON-LD instance

    Returns:
        True if graphs are isomorphic, False otherwise
    """
    from rdflib.compare import isomorphic

    context_path = ARTIFACTS_DIR / domain / f"{domain}{Extensions.CONTEXT}"
    if not context_path.exists():
        logger.error(
            "Context file not found: %s",
            normalize_path_for_display(context_path, ROOT_DIR),
        )
        return False

    if not instance_path.exists():
        logger.error(
            "Instance file not found: %s",
            normalize_path_for_display(instance_path, ROOT_DIR),
        )
        return False

    # Load context
    with open(context_path, "r", encoding="utf-8") as f:
        context_doc = json.load(f)
    context = context_doc.get("@context", {})

    # Load original instance
    with open(instance_path, "r", encoding="utf-8") as f:
        original = json.load(f)

    # Parse original to graph
    g_original = Graph(store=FAST_STORE)
    g_original.parse(data=json.dumps(original), format="json-ld")

    # Create compact version by replacing context (deep copy to avoid mutation)
    compact = copy.deepcopy(original)
    compact["@context"] = context

    # Parse compact to graph
    g_compact = Graph(store=FAST_STORE)
    try:
        g_compact.parse(data=json.dumps(compact), format="json-ld")
    except Exception as e:
        logger.error("Failed to parse compact instance: %s", e)
        return False

    # Compare
    if isomorphic(g_original, g_compact):
        logger.info("Round-trip test PASSED for %s", instance_path.name)
        return True
    else:
        logger.warning("Round-trip test FAILED for %s", instance_path.name)
        logger.debug("Original triples: %d", len(g_original))
        logger.debug("Compact triples: %d", len(g_compact))

        # Show differences
        original_triples = set(g_original)
        compact_triples = set(g_compact)
        missing = original_triples - compact_triples
        extra = compact_triples - original_triples

        if missing:
            logger.debug("Missing triples (in original, not in compact):")
            for t in list(missing)[:5]:
                logger.debug("  %s", t)
        if extra:
            logger.debug("Extra triples (in compact, not in original):")
            for t in list(extra)[:5]:
                logger.debug("  %s", t)

        return False


def _run_tests() -> bool:
    """Run self-tests for the module."""
    print("Running context_generator self-tests...")
    all_passed = True

    # Test 1: _build_ns_prefix_lookup / _lookup_prefix
    try:
        g = Graph()
        g.bind("gx", "https://w3id.org/gaia-x/development#")
        g.bind("manifest", "https://w3id.org/ascs-ev/envited-x/manifest/v5/")

        ns_lookup = _build_ns_prefix_lookup(g)
        assert _lookup_prefix(ns_lookup, "https://w3id.org/gaia-x/development#") == "gx"
        assert (
            _lookup_prefix(ns_lookup, "https://w3id.org/ascs-ev/envited-x/manifest/v5")
            == "manifest"
        )

        print("PASS: namespace prefix lookup")
    except AssertionError as e:
        print(f"FAIL: namespace prefix lookup - {e}")
        all_passed = False

    # Test 2: Generate context for manifest (if files exist)
    try:
        manifest_owl = ARTIFACTS_DIR / "manifest" / "manifest.owl.ttl"
        if manifest_owl.exists():
            context = generate_context("manifest")
            assert context is not None
            assert "@context" in context
            assert "manifest" in context["@context"]
            print("PASS: generate_context (manifest)")
        else:
            print("SKIP: generate_context (manifest files not found)")
    except AssertionError as e:
        print(f"FAIL: generate_context - {e}")
        all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests FAILED!")

    return all_passed


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate JSON-LD context files from OWL/SHACL artifacts"
    )
    parser.add_argument(
        "--domain",
        help="Generate context for a specific domain",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate contexts for all domains",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="Domains to exclude (default: gx)",
    )
    parser.add_argument(
        "--test-roundtrip",
        metavar="DOMAIN",
        help="Test round-trip equivalence for a domain",
    )
    parser.add_argument(
        "--instance",
        type=Path,
        help="Instance file for round-trip test",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        return 0 if success else 1

    if args.test_roundtrip:
        if not args.instance:
            # Try to find a valid instance
            test_dir = ROOT_DIR / "tests" / "data" / args.test_roundtrip / "valid"
            instances = list(test_dir.glob("*.json")) + list(test_dir.glob("*.jsonld"))
            if instances:
                args.instance = instances[0]
            else:
                print(f"No instance file found for {args.test_roundtrip}")
                return 1

        success = test_context_roundtrip(args.test_roundtrip, args.instance)
        return 0 if success else 1

    if args.all:
        results = generate_all_contexts(exclude=args.exclude, dry_run=args.dry_run)
        exclude_set = set(args.exclude) if args.exclude else {"gx"}
        written_count = sum(1 for p in results.values() if p is not None)
        total_count = len([d for d in results if d not in exclude_set])
        if args.dry_run:
            print(f"\nDry run: {total_count} context files would be generated")
        elif written_count > 0:
            print(f"\nUpdated {written_count}/{total_count} context files")
        else:
            print(f"\nAll {total_count} context files unchanged")
        return 0

    if args.domain:
        domain_dir = ARTIFACTS_DIR / args.domain
        if not domain_dir.is_dir():
            print(f"Unknown domain: {args.domain}")
            print(
                "Available: "
                + ", ".join(
                    d.name
                    for d in sorted(ARTIFACTS_DIR.iterdir())
                    if d.is_dir() and (d / f"{d.name}{Extensions.OWL}").exists()
                )
            )
            return 1

        context_doc = generate_context(args.domain)
        if context_doc:
            if args.dry_run:
                print(json.dumps(context_doc, indent=3))
            else:
                _write_context(args.domain, context_doc)
            return 0
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
