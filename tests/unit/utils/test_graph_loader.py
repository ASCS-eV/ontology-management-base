#!/usr/bin/env python3
"""
Unit tests for src.tools.utils.graph_loader.
"""

import json
import os
from pathlib import Path

import pytest
from rdflib import Graph, URIRef

from src.tools.utils import graph_loader
from src.tools.utils.registry_resolver import RegistryResolver


def test_load_graph_auto_detects_jsonld(temp_dir: Path):
    jsonld_file = temp_dir / "data.jsonld"
    jsonld_file.write_text(
        json.dumps(
            {
                "@context": {"ex": "http://example.org/"},
                "@id": "ex:a",
                "ex:prop": "value",
            }
        )
    )

    g = graph_loader.load_graph(jsonld_file)
    assert isinstance(g, Graph)
    assert len(g) >= 1


def test_load_graphs_combines_files(temp_dir: Path):
    a = temp_dir / "a.ttl"
    b = temp_dir / "b.ttl"
    a.write_text(
        "<http://example.org/a> <http://example.org/p> <http://example.org/o> ."
    )
    b.write_text(
        "<http://example.org/b> <http://example.org/p> <http://example.org/o> ."
    )

    g = graph_loader.load_graphs([a, b])
    assert len(g) == 2


def test_load_jsonld_files_extracts_prefixes(temp_dir: Path):
    jsonld_file = temp_dir / "data.json"
    jsonld_file.write_text(
        json.dumps(
            {
                "@context": {"ex": "http://example.org/"},
                "@id": "ex:thing",
                "ex:prop": "value",
            }
        )
    )

    g, prefixes = graph_loader.load_jsonld_files([jsonld_file], temp_dir)
    assert len(g) >= 1
    assert prefixes.get("ex") == "http://example.org/"


def test_load_turtle_files(temp_dir: Path):
    ttl_file = temp_dir / "data.ttl"
    ttl_file.write_text(
        "<http://example.org/a> <http://example.org/p> <http://example.org/o> ."
    )

    g = graph_loader.load_turtle_files([ttl_file], temp_dir)
    assert len(g) == 1


def test_load_turtle_files_missing_file_raises_file_not_found(temp_dir: Path):
    missing_file = temp_dir / "missing.ttl"

    with pytest.raises(FileNotFoundError, match="missing.ttl"):
        graph_loader.load_turtle_files([missing_file], temp_dir)


def test_load_turtle_files_invalid_turtle_raises_runtime_error(temp_dir: Path):
    ttl_file = temp_dir / "broken.ttl"
    ttl_file.write_text('@prefix ex: <http://example.org/> .\nex:subject "broken .\n')

    with pytest.raises(RuntimeError, match="broken.ttl"):
        graph_loader.load_turtle_files([ttl_file], temp_dir)


def test_load_jsonld_files_with_context_map_uses_public_id_when_cwd_unavailable(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    context_url = "https://example.org/test-context"
    jsonld_file = temp_dir / "data.json"
    context_file = temp_dir / "context.jsonld"

    context_file.write_text(
        json.dumps(
            {
                "@context": {
                    "@vocab": "http://example.org/",
                    "iri": {"@id": "http://example.org/iri", "@type": "@id"},
                }
            }
        )
    )
    jsonld_file.write_text(
        json.dumps(
            {
                "@context": context_url,
                "@id": "#thing",
                "iri": "./related.json",
            }
        )
    )

    def fail_getcwd() -> str:
        raise FileNotFoundError("cwd unavailable")

    monkeypatch.setattr(os, "getcwd", fail_getcwd)

    graph, prefixes = graph_loader.load_jsonld_files(
        [jsonld_file],
        temp_dir,
        context_url_map={context_url: context_file},
    )

    assert len(graph) >= 1
    assert prefixes == {}


def test_extract_external_iris_detects_did_web(temp_dir: Path):
    ttl_file = temp_dir / "data.ttl"
    ttl_file.write_text(
        "<did:web:test.example:thing> <http://example.org/p> <did:web:test.example:obj> ."
    )
    g = Graph()
    g.parse(str(ttl_file), format="turtle")
    iris = graph_loader.extract_external_iris(g)
    assert "did:web:test.example:thing" in iris
    assert "did:web:test.example:obj" in iris


def test_extract_external_iris_detects_resolver_mapped_fixture_iri(temp_dir: Path):
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )

    (temp_dir / "tests").mkdir()
    catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="did:ethr:test.fixture:entity" uri="tests/fixtures/entity.json" domain="fixture" test-type="fixture" category="fixture"/>
</catalog>
"""
    (temp_dir / "tests" / "catalog-v001.xml").write_text(catalog)
    fixtures_dir = temp_dir / "tests" / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "entity.json").write_text(
        json.dumps({"@id": "did:ethr:test.fixture:entity", "@type": "Fixture"})
    )

    ttl_file = temp_dir / "data.ttl"
    ttl_file.write_text(
        "<urn:test:credential> <http://example.org/issuer> <did:ethr:test.fixture:entity> ."
    )
    g = Graph()
    g.parse(str(ttl_file), format="turtle")

    resolver = RegistryResolver(temp_dir)
    iris = graph_loader.extract_external_iris(g, resolver=resolver)

    assert "did:ethr:test.fixture:entity" in iris


def test_load_fixtures_for_iris(temp_dir: Path):
    # Create minimal registry and catalog
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )

    (temp_dir / "tests").mkdir()
    catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="did:web:test.fixture:entity" uri="tests/fixtures/entity.json" domain="fixture" test-type="fixture" category="fixture"/>
</catalog>
"""
    (temp_dir / "tests" / "catalog-v001.xml").write_text(catalog)
    fixtures_dir = temp_dir / "tests" / "fixtures"
    fixtures_dir.mkdir()
    fixture_file = fixtures_dir / "entity.json"
    fixture_file.write_text(
        json.dumps(
            {
                "@id": "did:web:test.fixture:entity",
                "http://example.org/name": "Test Entity",
            }
        )
    )

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:test.fixture:entity"}, resolver, g, temp_dir
    )
    assert loaded == 1
    assert len(unresolved) == 0
    assert len(g) >= 1


def test_load_fixtures_for_iris_uses_context_url_map(temp_dir: Path):
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )

    (temp_dir / "tests").mkdir()
    catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="did:ethr:test.fixture:entity" uri="tests/fixtures/entity.json" domain="fixture" test-type="fixture" category="fixture"/>
</catalog>
"""
    (temp_dir / "tests" / "catalog-v001.xml").write_text(catalog)
    fixtures_dir = temp_dir / "tests" / "fixtures"
    fixtures_dir.mkdir()
    fixture_file = fixtures_dir / "entity.json"
    fixture_file.write_text(
        json.dumps(
            {
                "@context": "https://example.org/test-context",
                "@id": "did:ethr:test.fixture:entity",
                "name": "Fixture Entity",
            }
        )
    )

    contexts_dir = temp_dir / "contexts"
    contexts_dir.mkdir()
    local_context = contexts_dir / "test-context.jsonld"
    local_context.write_text(
        json.dumps(
            {
                "@context": {
                    "name": "http://example.org/name",
                    "@vocab": "http://example.org/",
                }
            }
        )
    )

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:ethr:test.fixture:entity"},
        resolver,
        g,
        temp_dir,
        context_url_map={"https://example.org/test-context": local_context},
    )

    assert loaded == 1
    assert len(unresolved) == 0
    assert len(g) >= 1


class _FakeUrlopenResponse:
    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeOpener:
    """Fake opener returned by monkeypatched build_opener."""

    def __init__(self, open_fn):
        self._open_fn = open_fn

    def open(self, request, timeout=10):
        return self._open_fn(request, timeout=timeout)


def _patch_opener(monkeypatch, open_fn):
    """Replace graph_loader.build_opener so it returns a _FakeOpener."""

    def fake_build_opener(*handlers):
        return _FakeOpener(open_fn)

    monkeypatch.setattr(graph_loader, "build_opener", fake_build_opener)


def test_load_fixtures_for_iris_resolves_did_web_online(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )
    (temp_dir / "artifacts").mkdir()
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>'
    )

    def fake_urlopen(request, timeout=10):
        assert request.full_url == "https://test.example/.well-known/did.json"
        return _FakeUrlopenResponse(
            json.dumps(
                {
                    "@context": {
                        "id": "@id",
                        "name": "http://example.org/name",
                    },
                    "id": "did:web:test.example",
                    "name": "Test Entity",
                }
            )
        )

    _patch_opener(monkeypatch, fake_urlopen)

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:test.example"},
        resolver,
        g,
        temp_dir,
        allow_online_fallback=True,
    )

    assert loaded == 1
    assert unresolved == []
    assert (URIRef("did:web:test.example"), None, None) in g


def test_load_fixtures_for_iris_resolves_did_web_online_with_context_url_map(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )
    (temp_dir / "artifacts").mkdir()
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>'
    )

    contexts_dir = temp_dir / "contexts"
    contexts_dir.mkdir()
    local_context = contexts_dir / "did-context.jsonld"
    local_context.write_text(
        json.dumps(
            {
                "@context": {
                    "id": "@id",
                    "name": "http://example.org/name",
                }
            }
        )
    )

    def fake_urlopen(request, timeout=10):
        assert request.full_url == "https://test.example/user/alice/did.json"
        return _FakeUrlopenResponse(
            json.dumps(
                {
                    "@context": "https://example.org/did-context",
                    "id": "did:web:test.example:user:alice",
                    "name": "Alice",
                }
            )
        )

    _patch_opener(monkeypatch, fake_urlopen)

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:test.example:user:alice"},
        resolver,
        g,
        temp_dir,
        context_url_map={"https://example.org/did-context": local_context},
        allow_online_fallback=True,
    )

    assert loaded == 1
    assert unresolved == []
    assert (URIRef("did:web:test.example:user:alice"), None, None) in g


def test_load_fixtures_for_iris_rejects_mismatched_did_document_id(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )
    (temp_dir / "artifacts").mkdir()
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>'
    )

    def fake_urlopen(request, timeout=10):
        assert request.full_url == "https://test.example/.well-known/did.json"
        return _FakeUrlopenResponse(
            json.dumps(
                {
                    "@context": {"id": "@id"},
                    "id": "did:web:other.example",
                }
            )
        )

    _patch_opener(monkeypatch, fake_urlopen)

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:test.example"},
        resolver,
        g,
        temp_dir,
    )

    assert loaded == 0
    assert unresolved == ["did:web:test.example"]
    assert len(g) == 0


def test_load_fixtures_for_iris_rejects_plain_did_json_without_context(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )
    (temp_dir / "artifacts").mkdir()
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>'
    )

    def fake_urlopen(request, timeout=10):
        assert request.full_url == "https://test.example/.well-known/did.json"
        return _FakeUrlopenResponse(json.dumps({"id": "did:web:test.example"}))

    _patch_opener(monkeypatch, fake_urlopen)

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:test.example"},
        resolver,
        g,
        temp_dir,
    )

    assert loaded == 0
    assert unresolved == ["did:web:test.example"]
    assert len(g) == 0


def test_load_fixtures_for_iris_rejects_ssrf_localhost(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    """Localhost did:web must never reach the network — did_web_to_url rejects it."""
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )
    (temp_dir / "artifacts").mkdir()
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>'
    )

    def should_not_be_called(request, timeout=10):
        raise AssertionError(f"SSRF: network call attempted to {request.full_url}")

    _patch_opener(monkeypatch, should_not_be_called)

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:localhost", "did:web:127.0.0.1", "did:web:169.254.169.254"},
        resolver,
        g,
        temp_dir,
    )

    assert loaded == 0
    assert len(unresolved) == 3
    assert len(g) == 0


def test_load_fixtures_for_iris_rejects_ssrf_private_ip(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    """Private IP did:web must never reach the network."""
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "registry.json").write_text(
        '{"version":"1.0.0","ontologies":{}}'
    )
    (temp_dir / "artifacts").mkdir()
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>'
    )

    def should_not_be_called(request, timeout=10):
        raise AssertionError(f"SSRF: network call attempted to {request.full_url}")

    _patch_opener(monkeypatch, should_not_be_called)

    resolver = RegistryResolver(temp_dir)
    g = Graph()
    loaded, unresolved = graph_loader.load_fixtures_for_iris(
        {"did:web:10.0.0.1", "did:web:192.168.1.1", "did:web:172.16.0.1"},
        resolver,
        g,
        temp_dir,
    )

    assert loaded == 0
    assert len(unresolved) == 3
    assert len(g) == 0
