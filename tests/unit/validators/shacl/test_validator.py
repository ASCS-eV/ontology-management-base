#!/usr/bin/env python3
"""
Unit tests for src.tools.validators.shacl.validator.
"""

from pathlib import Path

from rdflib import RDF, RDFS, Graph, Namespace

from src.tools.validators.shacl import validator as shacl_validator_module
from src.tools.validators.shacl.validator import ShaclValidator


def _make_validator(tmp: Path) -> ShaclValidator:
    # Minimal catalog files so RegistryResolver initializes without warnings
    (tmp / "docs").mkdir(parents=True, exist_ok=True)
    (tmp / "docs" / "registry.json").write_text('{"version":"1.0.0","ontologies":{}}')
    (tmp / "artifacts").mkdir(parents=True, exist_ok=True)
    (tmp / "artifacts" / "catalog-v001.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
"""
    )
    return ShaclValidator(tmp, inference_mode="none", verbose=False)


def test_apply_inference_none_includes_ontology(tmp_path: Path):
    ex = Namespace("http://example.org/")
    validator = _make_validator(tmp_path)

    data = Graph()
    ont = Graph()
    data.add((ex.a, RDF.type, ex.Type))
    ont.add((ex.Type, RDFS.subClassOf, ex.Super))

    combined, inferred = validator._apply_inference(data, ont)
    assert inferred == 0
    assert (ex.Type, RDFS.subClassOf, ex.Super) in combined


def test_apply_inference_rdfs_adds_inferred(tmp_path: Path):
    ex = Namespace("http://example.org/")
    validator = _make_validator(tmp_path)
    validator.inference_mode = "rdfs"

    data = Graph()
    ont = Graph()
    data.add((ex.a, RDF.type, ex.Sub))
    ont.add((ex.Sub, RDFS.subClassOf, ex.Super))

    combined, inferred = validator._apply_inference(data, ont)
    assert (ex.a, RDF.type, ex.Super) in combined
    assert inferred >= 1


def test_validate_data_conformance_registers_artifact_dirs(monkeypatch, temp_dir: Path):
    """Wrapper entrypoint registers artifact directories via resolver."""
    root = temp_dir / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "artifacts").mkdir(parents=True)
    (root / "imports").mkdir(parents=True)

    (root / "docs" / "registry.json").write_text('{"version":"1.0.0","ontologies":{}}')
    empty_catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
"""
    (root / "artifacts" / "catalog-v001.xml").write_text(empty_catalog)
    (root / "imports" / "catalog-v001.xml").write_text(empty_catalog)

    data_file = root / "data.json"
    data_file.write_text('{"@context":{"@vocab":"https://example.org/"}}')

    external_artifacts = temp_dir / "external-artifacts"
    (external_artifacts / "ext-domain").mkdir(parents=True)
    (external_artifacts / "ext-domain" / "ext-domain.owl.ttl").write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<https://example.org/ext-domain/v1> a owl:Ontology .\n"
    )
    (external_artifacts / "ext-domain" / "ext-domain.shacl.ttl").write_text(
        "@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
    )
    (external_artifacts / "ext-domain" / "ext-domain.context.jsonld").write_text(
        '{"@context":{"@vocab":"https://example.org/ext-domain/v1/"}}'
    )

    captured = {}

    class FakeValidator:
        def __init__(
            self,
            root_dir: Path,
            inference_mode: str = "rdfs",
            verbose: bool = True,
            resolver=None,
        ):
            captured["resolver"] = resolver
            self.resolver = resolver

        def validate(self, jsonld_files):
            captured["jsonld_files"] = jsonld_files
            return shacl_validator_module.ValidationResult(
                conforms=False,
                return_code=210,
                report_text="RAW",
                files_validated=["data.json"],
            )

        def format_result(self, _result):
            return "FORMATTED"

    monkeypatch.setattr(shacl_validator_module, "ShaclValidator", FakeValidator)

    return_code, output = shacl_validator_module.validate_data_conformance(
        [data_file],
        root,
        artifact_dirs=[external_artifacts],
    )

    assert return_code == 210
    assert output == "FORMATTED"
    assert captured["jsonld_files"] == [data_file]
    assert captured["resolver"] is not None
    assert "ext-domain" in captured["resolver"].get_artifact_domains()
