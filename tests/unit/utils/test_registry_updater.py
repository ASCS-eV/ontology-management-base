#!/usr/bin/env python3
"""
Unit tests for omb.utils.registry_updater.
"""

import json
import logging
from pathlib import Path

import pytest
import rdflib

from omb.utils import registry_updater


def test_clean_iri_strips_extension():
    iri = "https://example.org/onto/file.owl.ttl"
    cleaned = registry_updater.clean_iri(iri)
    assert cleaned.endswith("/")


def test_clean_iri_strips_hash_extension():
    iri = "https://w3id.org/gaia-x/development#gaia-x.owl.ttl"
    cleaned = registry_updater.clean_iri(iri)
    assert cleaned == "https://w3id.org/gaia-x/development#"


def test_determine_namespace_from_iri():
    iri = "https://w3id.org/ascs-ev/envited-x/hdmap/v5"
    assert registry_updater.determine_namespace_from_iri(iri) == "ascs-ev"


def test_extract_iri_from_graph_prefers_ontology():
    g = rdflib.Graph()
    onto = rdflib.URIRef("http://example.org/onto/v1")
    g.add((onto, rdflib.RDF.type, rdflib.OWL.Ontology))
    assert registry_updater.extract_iri_from_graph(g) == str(onto)


def test_generate_xml_catalog_includes_entries(temp_dir: Path):
    # Create minimal ontology file
    ontology_file = temp_dir / "demo.owl.ttl"
    ontology_file.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<http://example.org/demo/v1> a owl:Ontology .\n"
    )

    # Create minimal shacl file with owl:Ontology
    shacl_file = temp_dir / "demo.shacl.ttl"
    shacl_file.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<http://example.org/demo/v1/shapes> a owl:Ontology .\n"
    )

    context_file = temp_dir / "demo.context.jsonld"
    context_file.write_text("{}")

    ontologies = {
        "demo": {
            "ontology": ontology_file,
            "shacl": [shacl_file],
            "jsonld": context_file,
            "properties": None,
            "instance": None,
        }
    }
    registry = {
        "ontologies": {
            "demo": {
                "iri": "http://example.org/demo/v1",
                "latest": "v1",
                "versions": {"v1": {"files": {}}},
            }
        }
    }

    xml = registry_updater.generate_xml_catalog(
        ontologies, registry, temp_dir / "catalog-v001.xml"
    )
    assert "http://example.org/demo/v1" in xml
    assert "http://example.org/demo/v1/shapes" in xml
    assert "http://example.org/demo/v1/context" in xml


def test_extract_catalog_hints_returns_none_when_no_file(temp_dir: Path):
    owl_file = temp_dir / "demo.owl.ttl"
    owl_file.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<http://example.org/demo/v1> a owl:Ontology .\n"
    )
    result = registry_updater.extract_catalog_hints(owl_file)
    assert result is None


def test_extract_catalog_hints_reads_context_iris(temp_dir: Path):
    owl_file = temp_dir / "demo.owl.ttl"
    owl_file.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<http://example.org/demo/v1> a owl:Ontology .\n"
    )
    hints_file = temp_dir / "demo.catalog-hints.ttl"
    hints_file.write_text(
        "@prefix jsonld: <http://www.w3.org/ns/json-ld#> .\n"
        "<http://example.org/demo/context/v1> a jsonld:Context .\n"
    )
    result = registry_updater.extract_catalog_hints(owl_file)
    assert result == ["http://example.org/demo/context/v1"]


def test_generate_imports_catalog_uses_hints_over_owl(temp_dir: Path):
    """Catalog hints override cross-domain context declarations in OWL files."""
    domain_dir = temp_dir / "sec"
    domain_dir.mkdir()

    owl_file = domain_dir / "sec.owl.ttl"
    owl_file.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix jsonld: <http://www.w3.org/ns/json-ld#> .\n"
        "<https://w3id.org/security#> a owl:Ontology .\n"
        # Cross-domain context — should be ignored when hints exist
        "<https://www.w3.org/ns/credentials/v2> a jsonld:Context .\n"
    )

    hints_file = domain_dir / "sec.catalog-hints.ttl"
    hints_file.write_text(
        "@prefix jsonld: <http://www.w3.org/ns/json-ld#> .\n"
        "<https://w3id.org/security/suites/secp256k1recovery-2020/v2>"
        " a jsonld:Context .\n"
    )

    context_file = domain_dir / "sec.context.jsonld"
    context_file.write_text("{}")

    bundles = {
        "sec": {
            "ontology": owl_file,
            "shacl": [],
            "jsonld": context_file,
            "properties": None,
            "instance": None,
        }
    }

    xml = registry_updater.generate_imports_catalog(
        bundles, temp_dir / "catalog-v001.xml"
    )
    # Hints context should be present
    assert "secp256k1recovery-2020/v2" in xml
    # Cross-domain context should NOT be present
    assert "credentials/v2" not in xml


def test_generate_imports_catalog_falls_back_to_owl_context(temp_dir: Path):
    """Without hints, context IRIs come from OWL file declarations."""
    domain_dir = temp_dir / "cred"
    domain_dir.mkdir()

    owl_file = domain_dir / "cred.owl.ttl"
    owl_file.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix jsonld: <http://www.w3.org/ns/json-ld#> .\n"
        "<https://www.w3.org/2018/credentials#> a owl:Ontology .\n"
        "<https://www.w3.org/ns/credentials/v2> a jsonld:Context .\n"
    )

    context_file = domain_dir / "cred.context.jsonld"
    context_file.write_text("{}")

    bundles = {
        "cred": {
            "ontology": owl_file,
            "shacl": [],
            "jsonld": context_file,
            "properties": None,
            "instance": None,
        }
    }

    xml = registry_updater.generate_imports_catalog(
        bundles, temp_dir / "catalog-v001.xml"
    )
    assert "https://www.w3.org/ns/credentials/v2" in xml


def _seed_registry(path: Path, release_tag: str, generated: str) -> None:
    """Write a registry whose content matches what update_registry() builds."""
    path.write_text(
        json.dumps(
            {
                "version": registry_updater.REGISTRY_VERSION,
                "latestRelease": release_tag,
                "ontologies": {},
                "generated": generated,
            },
            indent=3,
        )
        + "\n",
        encoding="utf-8",
    )


def test_update_registry_carries_generated_forward_when_content_unchanged(
    temp_dir: Path, monkeypatch
):
    """An unchanged registry keeps its timestamp instead of dropping it."""
    registry_path = temp_dir / "registry.json"
    stamp = "2020-01-01T00:00:00+00:00"
    _seed_registry(registry_path, "v1.0.0", stamp)
    monkeypatch.setattr(registry_updater, "REGISTRY_PATH", registry_path)

    registry = registry_updater.update_registry("v1.0.0", {})

    assert registry["generated"] == stamp


def test_update_registry_refreshes_generated_when_content_changes(
    temp_dir: Path, monkeypatch
):
    """A changed release tag refreshes the timestamp."""
    registry_path = temp_dir / "registry.json"
    stamp = "2020-01-01T00:00:00+00:00"
    _seed_registry(registry_path, "v1.0.0", stamp)
    monkeypatch.setattr(registry_updater, "REGISTRY_PATH", registry_path)

    registry = registry_updater.update_registry("v2.0.0", {})

    assert registry["latestRelease"] == "v2.0.0"
    assert registry["generated"] != stamp


def test_update_registry_is_idempotent_across_runs(temp_dir: Path, monkeypatch):
    """Regenerating an up-to-date registry rewrites nothing."""
    registry_path = temp_dir / "registry.json"
    monkeypatch.setattr(registry_updater, "REGISTRY_PATH", registry_path)

    registry_updater.write_registry(registry_updater.update_registry("v1.0.0", {}))
    first = registry_path.read_text(encoding="utf-8")
    assert "generated" in json.loads(first)

    registry_updater.write_registry(registry_updater.update_registry("v1.0.0", {}))

    assert registry_path.read_text(encoding="utf-8") == first


def _write_json(path: Path, document: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.mark.parametrize("reverse", [False, True], ids=["listed-in-order", "reversed"])
def test_discover_test_data_maps_a_shared_iri_to_the_first_path(
    temp_dir: Path, monkeypatch, caplog, reverse: bool
):
    """An IRI two files describe maps to the same file whatever the walk order."""
    data_dir = temp_dir / "tests" / "data" / "demo" / "valid"
    first = _write_json(
        data_dir / "a_catalog.json",
        {"@graph": [{"@id": "urn:example:asset"}, {"@id": "urn:example:catalog"}]},
    )
    second = _write_json(
        data_dir / "b_run.json",
        {"@graph": [{"@id": "urn:example:run"}, {"@id": "urn:example:asset"}]},
    )
    walk = [second, first] if reverse else [first, second]
    monkeypatch.setattr(registry_updater, "ROOT_DIR", temp_dir)
    monkeypatch.setattr(registry_updater, "TESTS_DATA_DIR", temp_dir / "tests" / "data")
    monkeypatch.setattr(registry_updater, "collect_jsonld_files", lambda *a, **k: walk)
    caplog.set_level(logging.WARNING)

    test_data = registry_updater.discover_test_data()

    assert {iri: entry["path"] for iri, entry in test_data.items()} == {
        "urn:example:asset": "tests/data/demo/valid/a_catalog.json",
        "urn:example:catalog": "tests/data/demo/valid/a_catalog.json",
        "urn:example:run": "tests/data/demo/valid/b_run.json",
    }
    assert "Duplicate test-data IRI urn:example:asset" in caplog.text


@pytest.mark.parametrize("reverse", [False, True], ids=["listed-in-order", "reversed"])
def test_discover_fixtures_maps_a_shared_iri_to_the_first_path(
    temp_dir: Path, monkeypatch, caplog, reverse: bool
):
    """An IRI two fixtures claim maps to the same fixture whatever the walk order."""
    fixtures_dir = temp_dir / "tests" / "fixtures"
    first = _write_json(fixtures_dir / "a-did.json", {"@id": "did:web:example.org"})
    second = _write_json(fixtures_dir / "b-did.json", {"@id": "did:web:example.org"})
    walk = [second, first] if reverse else [first, second]
    monkeypatch.setattr(registry_updater, "FIXTURES_DIR", fixtures_dir)
    monkeypatch.setattr(registry_updater, "collect_jsonld_files", lambda *a, **k: walk)
    caplog.set_level(logging.WARNING)

    assert registry_updater.discover_fixtures() == {"did:web:example.org": "a-did.json"}
    assert "Duplicate fixture IRI did:web:example.org" in caplog.text
