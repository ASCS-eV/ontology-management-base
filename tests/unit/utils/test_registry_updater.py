#!/usr/bin/env python3
"""
Unit tests for src.tools.utils.registry_updater.
"""

from pathlib import Path

import rdflib

from src.tools.utils import registry_updater


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
