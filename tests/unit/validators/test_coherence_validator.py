#!/usr/bin/env python3
"""
Unit tests for coherence_validator behavior.
"""

from pathlib import Path

from src.tools.core.iri_utils import get_local_name
from src.tools.core.result import ReturnCodes
from src.tools.validators.coherence_validator import (
    extract_ontology_classes,
    extract_shacl_classes_from_file,
    validate_artifact_coherence,
)


def _write_registry(root: Path) -> None:
    registry_path = root / "docs" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text('{"version": "1.0.0", "ontologies": {}}')


def _write_artifacts_catalog(root: Path, content: str) -> None:
    catalog_path = root / "artifacts" / "catalog-v001.xml"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(content)


def test_coherence_fails_when_shacl_missing(temp_dir: Path) -> None:
    _write_registry(temp_dir)

    artifacts_catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://example.org/demo/v1" uri="demo/demo.owl.ttl"/>
</catalog>
"""
    _write_artifacts_catalog(temp_dir, artifacts_catalog)

    # No SHACL entries for demo -> should fail
    return_code, message = validate_artifact_coherence("demo", root_dir=temp_dir)

    assert return_code == ReturnCodes.COHERENCE_ERROR
    assert "No SHACL file found" in message


def test_get_local_name_variants():
    # coherence_validator uses get_local_name with lowercase=True
    # but the imported function preserves case by default
    assert get_local_name("http://example.org/a#B", lowercase=True) == "b"
    assert get_local_name("http://example.org/a/B", lowercase=True) == "b"
    # Without lowercase, case is preserved
    assert get_local_name("http://example.org/a#B") == "B"
    assert get_local_name("http://example.org/a/B") == "B"


def test_extract_shacl_classes_from_file(temp_dir: Path):
    ttl = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
ex:Shape a sh:NodeShape ;
  sh:targetClass ex:Thing .
"""
    shacl_file = temp_dir / "shape.shacl.ttl"
    shacl_file.write_text(ttl)
    classes = extract_shacl_classes_from_file(str(shacl_file))
    assert "thing" in classes


def test_extract_ontology_classes(temp_dir: Path):
    ttl = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .
ex:Thing a owl:Class .
"""
    owl_file = temp_dir / "demo.owl.ttl"
    owl_file.write_text(ttl)
    classes = extract_ontology_classes(str(owl_file))
    assert "thing" in classes


def _build_coherent_repo(root: Path, extra_shacl_target: str = None) -> None:
    """Build a minimal repo with OWL + SHACL artifacts for domain 'demo'."""
    _write_registry(root)

    owl_ttl = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .
ex:Thing a owl:Class .
"""
    shacl_target = extra_shacl_target or "ex:Thing"
    shacl_ttl = f"""@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
ex:ThingShape a sh:NodeShape ;
  sh:targetClass {shacl_target} .
"""
    artifacts = root / "artifacts" / "demo"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "demo.owl.ttl").write_text(owl_ttl)
    (artifacts / "demo.shacl.ttl").write_text(shacl_ttl)

    catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://example.org/demo/v1" uri="demo/demo.owl.ttl"/>
  <uri name="http://example.org/demo/v1/shacl" uri="demo/demo.shacl.ttl"/>
</catalog>
"""
    _write_artifacts_catalog(root, catalog)


def test_coherence_known_issues_excluded(temp_dir: Path) -> None:
    """Known upstream issues are excluded from failure and reported as warnings."""
    _build_coherent_repo(temp_dir, extra_shacl_target="ex:Missing")

    # Without known_issues, this should fail
    rc_fail, msg_fail = validate_artifact_coherence("demo", root_dir=temp_dir)
    assert rc_fail == ReturnCodes.COHERENCE_ERROR
    assert "missing" in msg_fail.lower()

    # With known_issues containing the missing class, it should pass
    rc_pass, msg_pass = validate_artifact_coherence(
        "demo", root_dir=temp_dir, known_issues={"missing"}
    )
    assert rc_pass == ReturnCodes.SUCCESS
    assert "Known upstream issue" in msg_pass
    assert "missing" in msg_pass
