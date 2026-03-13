#!/usr/bin/env python3
"""Tests for local JSON-LD context resolution."""

from pathlib import Path

from src.tools.utils.context_resolver import build_context_url_map
from src.tools.utils.registry_resolver import RegistryResolver


def test_build_context_url_map_includes_schema_shared_w3c_contexts(root_dir: Path):
    """Shared W3C contexts served by schema.context.jsonld are mapped locally."""
    resolver = RegistryResolver(root_dir)

    url_map = build_context_url_map(resolver, root_dir)

    schema_context_path = (
        root_dir / "imports" / "schema" / "schema.context.jsonld"
    ).resolve()

    assert url_map["http://www.w3.org/2006/vcard/ns#"] == schema_context_path
    assert url_map["http://www.w3.org/ns/dcat#"] == schema_context_path
