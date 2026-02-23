"""Local JSON-LD context resolver using catalog-based discovery.

rdflib's built-in JSON-LD parser fetches remote @context URLs via urllib,
which fails in WSL (TLS errors) and before GitHub Pages publication.

This module inlines context content directly into JSON-LD data before
parsing, avoiding any network access for known contexts.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.tools.core.iri_utils import iri_variants
from src.tools.core.logging import get_logger

logger = get_logger(__name__)

# URI tweaks applied when inlining context files.
# Empty by default — generated artifacts use native IRIs from LinkML.
DEFAULT_URI_TWEAKS: Dict[str, str] = {}


def _add_url_variants(url_map: Dict[str, Path], iri: str, abs_path: Path) -> None:
    """Add URL variants for an IRI to the URL map.

    Handles the mismatch between ``#``-fragment and ``/``-slash IRIs
    using the centralized ``iri_variants()`` utility.
    """
    for variant in iri_variants(iri):
        url_map[variant] = abs_path


def build_context_url_map(resolver, root_dir: Path) -> Dict[str, Path]:
    """
    Build URL -> local file mapping from the registry resolver.

    Uses the artifacts catalog to map ontology IRIs to their local
    JSON-LD context files, enabling offline context resolution.

    Args:
        resolver: RegistryResolver instance
        root_dir: Repository root directory (for resolving relative paths)

    Returns:
        Dictionary mapping context URLs to absolute local file paths
    """
    url_map: Dict[str, Path] = {}
    for domain in resolver.list_domains():
        iri = resolver.get_iri(domain)
        context_rel = resolver.get_context_path(domain)
        if iri and context_rel:
            abs_path = (root_dir / context_rel).resolve()
            if abs_path.exists():
                _add_url_variants(url_map, iri, abs_path)
    # Import contexts are resolved from imports/catalog-v001.xml
    for iri, context_rel in resolver.get_import_context_mappings().items():
        abs_path = (root_dir / context_rel).resolve()
        if abs_path.exists():
            _add_url_variants(url_map, iri, abs_path)
    return url_map


def discover_context_files(
    artifact_dirs: List[Path],
    uri_tweaks: Optional[Dict[str, str]] = None,
) -> Dict[str, Path]:
    """
    Discover context files from artifact directories and build URL mappings.

    Scans for ``*.context.jsonld`` files, reads their ``@vocab`` to determine
    the IRI they serve, and builds URL -> local-path mappings.

    Args:
        artifact_dirs: List of directories to scan for context files
        uri_tweaks: Optional dict of IRI replacements applied to ``@vocab``
            values before mapping (handles Gaia-X ``#`` → ``/``).

    Returns:
        Dictionary mapping context URLs to absolute local file paths
    """
    url_map: Dict[str, Path] = {}
    for artifacts_dir in artifact_dirs:
        if not artifacts_dir.is_dir():
            continue
        for ctx_file in artifacts_dir.rglob("*.context.jsonld"):
            try:
                with open(ctx_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                context = data.get("@context", {})
                if isinstance(context, dict):
                    vocab = context.get("@vocab")
                elif isinstance(context, list):
                    vocab = None
                    for entry in context:
                        if isinstance(entry, dict) and "@vocab" in entry:
                            vocab = entry["@vocab"]
                            break
                else:
                    vocab = None

                if vocab:
                    abs_path = ctx_file.resolve()
                    _add_url_variants(url_map, vocab, abs_path)
                    # Also map the tweaked variant (e.g. # -> /)
                    if uri_tweaks:
                        tweaked = vocab
                        for old, new in uri_tweaks.items():
                            tweaked = tweaked.replace(old, new)
                        if tweaked != vocab:
                            _add_url_variants(url_map, tweaked, abs_path)
                    logger.debug("Discovered context: %s -> %s", vocab, abs_path)
            except Exception as e:
                logger.debug("Could not read context file %s: %s", ctx_file, e)
    return url_map


def _load_and_tweak_context(local_path: Path, uri_tweaks: Dict[str, str]) -> dict:
    """Load a context file and apply URI tweaks to its serialised content."""
    with open(local_path, "r", encoding="utf-8") as f:
        raw = f.read()
    for old, new in uri_tweaks.items():
        raw = raw.replace(old, new)
    data = json.loads(raw)
    # Return just the @context value, not the wrapper
    ctx = data.get("@context", data)
    return ctx


def _inline_context_value(
    value: Union[str, list, dict],
    url_map: Dict[str, Path],
    uri_tweaks: Dict[str, str],
) -> Union[str, list, dict]:
    """Replace a context URL with the inlined context object content."""
    if isinstance(value, str):
        local_path = url_map.get(value) or url_map.get(value.rstrip("/"))
        if local_path and local_path.exists():
            logger.debug("Inlining context: %s from %s", value, local_path)
            return _load_and_tweak_context(local_path, uri_tweaks)
        return value
    elif isinstance(value, list):
        return [_inline_context_value(item, url_map, uri_tweaks) for item in value]
    elif isinstance(value, dict):
        return _inline_contexts_recursive(value, url_map, uri_tweaks)
    return value


def _inline_contexts_recursive(
    data: Union[dict, list],
    url_map: Dict[str, Path],
    uri_tweaks: Dict[str, str],
) -> Union[dict, list]:
    """Recursively walk JSON-LD and inline @context URL references."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "@context":
                result[key] = _inline_context_value(value, url_map, uri_tweaks)
            else:
                result[key] = _inline_contexts_recursive(value, url_map, uri_tweaks)
        return result
    elif isinstance(data, list):
        return [_inline_contexts_recursive(item, url_map, uri_tweaks) for item in data]
    return data


def _collect_unresolved_context_urls(
    data: Union[dict, list],
    url_map: Dict[str, Path],
) -> List[str]:
    """Collect remote @context URLs that could not be inlined locally."""
    unresolved: set[str] = set()

    def _walk(node: Union[dict, list, str], in_context: bool = False) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                _walk(value, in_context=(key == "@context"))
            return
        if isinstance(node, list):
            for item in node:
                _walk(item, in_context=in_context)
            return
        if (
            isinstance(node, str)
            and in_context
            and node.startswith(("http://", "https://"))
        ):
            if not (url_map.get(node) or url_map.get(node.rstrip("/"))):
                unresolved.add(node)

    _walk(data)
    return sorted(unresolved)


def load_jsonld_with_local_contexts(
    file_path: Path,
    url_map: Optional[Dict[str, Path]],
    uri_tweaks: Optional[Dict[str, str]] = None,
) -> str:
    """
    Load a JSON-LD file, inline known contexts, and apply URI tweaks.

    Instead of rewriting context URLs to ``file://`` URIs (which rdflib
    would still fetch and parse with ``#``-fragment IRIs), this function
    *inlines* the context content directly into the JSON-LD structure.
    This ensures URI tweaks are applied to context content too.

    Args:
        file_path: Path to the JSON-LD file
        url_map: Context URL -> local file mapping (None to skip)
        uri_tweaks: IRI replacements. Defaults to ``DEFAULT_URI_TWEAKS``.

    Returns:
        JSON string ready for rdflib parsing
    """
    if uri_tweaks is None:
        uri_tweaks = DEFAULT_URI_TWEAKS

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if url_map:
        data = _inline_contexts_recursive(data, url_map, uri_tweaks)
        unresolved = _collect_unresolved_context_urls(data, url_map)
        if unresolved:
            logger.warning(
                "Unresolved @context URL(s) in %s (rdflib will fetch remotely): %s",
                file_path,
                ", ".join(unresolved),
            )

    result = json.dumps(data)

    # Also apply URI tweaks to the main document content
    for old, new in uri_tweaks.items():
        result = result.replace(old, new)

    return result
