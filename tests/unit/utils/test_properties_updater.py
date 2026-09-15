#!/usr/bin/env python3
"""
Unit tests for omb.utils.properties_updater.
"""

import json
from pathlib import Path

import pytest

from omb.utils import properties_updater


def test_extract_shacl_properties_from_ttl(temp_dir: Path):
    ttl = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .

ex:Shape a sh:NodeShape ;
  sh:property [
    sh:path ex:prop ;
    sh:minCount 1 ;
    sh:maxCount 2 ;
    sh:description "desc" ;
    sh:datatype ex:Type ;
  ] .
"""
    file_path = temp_dir / "shape.shacl.ttl"
    file_path.write_text(ttl)

    graph = properties_updater.parse_graph(file_path, "turtle")
    props = properties_updater.extract_shacl_properties(graph, "shape.shacl.ttl")

    assert len(props) == 1
    assert str(props[0].path).endswith("prop")
    assert str(props[0].shape).endswith("Shape")
    assert str(props[0].min_count) == "1"
    assert str(props[0].max_count) == "2"
    assert props[0].filename == "shape.shacl.ttl"


def test_prefix_helpers(temp_dir: Path):
    ttl = "@prefix ex: <http://example.org/> .\nex:Thing ex:prop ex:Other .\n"
    file_path = temp_dir / "data.ttl"
    file_path.write_text(ttl)

    graph = properties_updater.parse_graph(file_path, "turtle")
    prefixes = properties_updater.extract_prefixes(graph)
    assert "http://example.org/" in prefixes

    uri = "http://example.org/Thing"
    replaced = properties_updater._replace_with_prefix(
        uri, {"http://example.org/": "ex"}
    )
    assert replaced == ("ex", "Thing")


def test_parse_graph_preserves_authored_schema_prefix(temp_dir: Path):
    ttl = """@prefix schema: <https://schema.org/> .
@prefix ex: <http://example.org/> .

ex:Thing schema:name "Example" .
"""
    file_path = temp_dir / "data.ttl"
    file_path.write_text(ttl)

    graph = properties_updater.parse_graph(file_path, "turtle")
    prefixes = properties_updater.extract_prefixes(graph)

    assert prefixes["https://schema.org/"] == "schema"
    assert "http://schema.org/" not in prefixes


@pytest.fixture
def external_documentation_artifacts(tmp_path):
    artifacts = tmp_path / "caller-artifacts"
    domain = artifacts / "demo"
    domain.mkdir(parents=True)
    (domain / "demo.owl.ttl").write_text(
        "@prefix ex: <https://example.org/demo/> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        'ex: a owl:Ontology; owl:versionInfo "1.2" .\n'
        'ex:Thing a owl:Class; rdfs:label "Straße"@de .\n',
        encoding="utf-8",
    )
    (domain / "demo.shacl.ttl").write_text(
        "@prefix ex: <https://example.org/demo/> .\n"
        "@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
        "ex:Shape a sh:NodeShape; sh:targetClass ex:Thing;\n"
        ' sh:property [ sh:path ex:name; sh:description "Straßenname"@de ] .\n',
        encoding="utf-8",
    )
    return artifacts


def test_main_external_input_creates_complete_documentation(
    external_documentation_artifacts, tmp_path
):
    artifacts = external_documentation_artifacts
    output = tmp_path / "output"
    before = {p: p.read_bytes() for p in artifacts.rglob("*") if p.is_file()}

    assert (
        properties_updater.main(
            ["--artifacts", str(artifacts), "--output", str(output)]
        )
        == 0
    )

    properties = output / "artifacts/demo/PROPERTIES.md"
    assert "Straße" in properties.read_text(encoding="utf-8")
    assert "Straßenname" in properties.read_text(encoding="utf-8")
    catalog = (output / "docs/ontologies/catalog.md").read_text(encoding="utf-8")
    assert "|demo|v1.2|" in catalog
    page = (output / "docs/ontologies/properties/demo.md").read_text(encoding="utf-8")
    assert '--8<-- "artifacts/demo/v1.2/PROPERTIES.md"' in page
    staged = output / "docs/artifacts/demo/v1.2"
    assert (staged / "PROPERTIES.md").read_bytes() == properties.read_bytes()
    for name in ("demo.owl.ttl", "demo.shacl.ttl"):
        assert (staged / name).read_bytes() == (artifacts / "demo" / name).read_bytes()
    assert (output / "docs/ontologies/properties.md").is_file()
    assert {p: p.read_bytes() for p in artifacts.rglob("*") if p.is_file()} == before


def test_main_preserves_existing_catalog_comments(
    external_documentation_artifacts, tmp_path
):
    output = tmp_path / "output"
    catalog = output / "docs/ontologies/catalog.md"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        "# Authored introduction\n<!-- custom comment -->\n"
        "<!-- START_REGISTRY_TABLE -->\nstale table\n<!-- END_REGISTRY_TABLE -->\n"
        "Keep this conclusion.\n",
        encoding="utf-8",
    )
    assert (
        properties_updater.main(
            [
                "--artifacts",
                str(external_documentation_artifacts),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    content = catalog.read_text(encoding="utf-8")
    assert content.startswith("# Authored introduction\n<!-- custom comment -->\n")
    assert content.endswith("Keep this conclusion.\n")
    assert "stale table" not in content


def test_update_catalog_missing_markers_preserves_authored_page(tmp_path):
    catalog = tmp_path / "catalog.md"
    catalog.write_text("# Hand-authored catalog", encoding="utf-8")
    with pytest.raises(ValueError, match="markers"):
        properties_updater.update_catalog_table(catalog, "new table", create=True)
    assert catalog.read_text(encoding="utf-8") == "# Hand-authored catalog"


@pytest.mark.parametrize("failure", ["missing", "empty", "malformed"])
def test_main_invalid_artifacts_returns_error(
    external_documentation_artifacts, tmp_path, failure
):
    artifacts = external_documentation_artifacts
    if failure == "missing":
        artifacts = tmp_path / "missing"
    elif failure == "empty":
        artifacts = tmp_path / "empty"
        artifacts.mkdir()
    else:
        (artifacts / "demo/demo.shacl.ttl").write_text("not Turtle", encoding="utf-8")
    assert (
        properties_updater.main(
            ["--artifacts", str(artifacts), "--output", str(tmp_path / "output")]
        )
        == 1
    )
    assert not (tmp_path / "output").exists()


def test_main_external_default_output_is_cwd(
    external_documentation_artifacts, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    assert (
        properties_updater.main(["--artifacts", str(external_documentation_artifacts)])
        == 0
    )
    assert (tmp_path / "generated-docs/docs/ontologies/catalog.md").is_file()
    assert not (external_documentation_artifacts / "demo/PROPERTIES.md").exists()


def test_main_source_defaults_preserve_release_registry(
    external_documentation_artifacts, tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "omb").mkdir()
    (source / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    artifacts = source / "artifacts"
    external_documentation_artifacts.rename(artifacts)
    docs = source / "docs"
    catalog = docs / "ontologies/catalog.md"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        "# Contributor catalog\n<!-- preserve me -->\n"
        "<!-- START_REGISTRY_TABLE -->\nold\n<!-- END_REGISTRY_TABLE -->\n",
        encoding="utf-8",
    )
    registry = {
        "ontologies": {
            "demo": {
                "latest": "v99",
                "versions": {
                    "v99": {
                        "files": {
                            "ontology": "artifacts/demo/demo.owl.ttl",
                            "properties": "artifacts/demo/PROPERTIES.md",
                        }
                    }
                },
            }
        },
    }
    registry_path = docs / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    original_registry = registry_path.read_bytes()
    monkeypatch.setattr(properties_updater, "ROOT_DIR", source)
    monkeypatch.setattr(properties_updater, "ARTIFACTS_DIR", artifacts)
    monkeypatch.setattr(properties_updater, "REGISTRY_PATH", registry_path)

    assert properties_updater.main([]) == 0

    assert registry_path.read_bytes() == original_registry
    assert (artifacts / "demo/PROPERTIES.md").is_file()
    content = catalog.read_text(encoding="utf-8")
    assert "<!-- preserve me -->" in content
    assert "|demo|v99|" in content
    assert "Version: `v99`" in (docs / "ontologies/properties/demo.md").read_text(
        encoding="utf-8"
    )
