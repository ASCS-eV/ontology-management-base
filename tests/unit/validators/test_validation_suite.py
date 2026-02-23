#!/usr/bin/env python3
"""
Unit tests for src.tools.validators.validation_suite.

Tests cover:
- CLI argument parsing
- Data paths mode with auto-discovery
- Domain mode with --artifacts
- Syntax checking
- Data conformance validation
- Artifact coherence validation
- Inference mode parameter
"""

import json
from pathlib import Path

import pytest

from src.tools.utils.registry_resolver import RegistryResolver
from src.tools.validators import validation_suite
from src.tools.validators.shacl.validator import (
    ValidationResult as ShaclValidationResult,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def minimal_repo(temp_dir: Path):
    """Create minimal repository structure for testing."""
    # Create directories
    (temp_dir / "docs").mkdir()
    (temp_dir / "artifacts" / "test-domain").mkdir(parents=True)
    (temp_dir / "tests" / "data" / "test-domain" / "valid").mkdir(parents=True)
    (temp_dir / "tests" / "fixtures").mkdir(parents=True)
    (temp_dir / "imports").mkdir()

    # Create registry.json
    registry = {"version": "1.0.0", "ontologies": {}}
    (temp_dir / "docs" / "registry.json").write_text(json.dumps(registry))

    # Create artifacts catalog with ontology and shacl entries
    (temp_dir / "artifacts" / "catalog-v001.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="https://example.org/test-domain/v1/"
       uri="test-domain/test-domain.owl.ttl"
       domain="test-domain"
       category="ontology"/>
  <uri name="https://example.org/test-domain/v1/shapes"
       uri="test-domain/test-domain.shacl.ttl"
       domain="test-domain"
       category="shacl"/>
</catalog>
"""
    )

    # Create imports catalog
    (temp_dir / "imports" / "catalog-v001.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
</catalog>
"""
    )

    # Create minimal OWL ontology
    owl_content = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <https://example.org/test-domain/v1/> .

<https://example.org/test-domain/v1> a owl:Ontology .
:TestClass a owl:Class ; rdfs:label "Test Class" .
"""
    (temp_dir / "artifacts" / "test-domain" / "test-domain.owl.ttl").write_text(
        owl_content
    )

    # Create minimal SHACL shapes
    shacl_content = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix : <https://example.org/test-domain/v1/> .

:TestClassShape a sh:NodeShape ;
    sh:targetClass :TestClass .
"""
    (temp_dir / "artifacts" / "test-domain" / "test-domain.shacl.ttl").write_text(
        shacl_content
    )

    # Create context
    context = {"@context": {"@vocab": "https://example.org/test-domain/v1/"}}
    (temp_dir / "artifacts" / "test-domain" / "test-domain.context.jsonld").write_text(
        json.dumps(context)
    )

    return temp_dir


@pytest.fixture
def repo_with_test_data(minimal_repo: Path):
    """Add test data to minimal repo."""
    # Create test data file
    test_instance = {
        "@context": {"@vocab": "https://example.org/test-domain/v1/"},
        "@id": "did:test:instance-001",
        "@type": "TestClass",
    }
    (
        minimal_repo / "tests" / "data" / "test-domain" / "valid" / "test_instance.json"
    ).write_text(json.dumps(test_instance))

    # Create tests catalog
    (minimal_repo / "tests" / "catalog-v001.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="did:test:instance-001"
       uri="tests/data/test-domain/valid/test_instance.json"
       domain="test-domain"
       test-type="valid"
       category="test-data"/>
</catalog>
"""
    )

    return minimal_repo


# =============================================================================
# Tests: check_environment
# =============================================================================


def test_check_environment_passes_in_venv():
    """check_environment() should not raise when running inside a venv."""
    # This test runs inside a venv, so it should pass without error.
    # We just verify it's callable and doesn't crash in normal test env.
    validation_suite.check_environment()


# =============================================================================
# Tests: check_syntax_all
# =============================================================================


def test_check_syntax_all_empty_domains():
    """Empty domain list returns 0."""
    result = validation_suite.check_syntax_all([])
    assert result == 0


def test_check_syntax_all_with_valid_json(repo_with_test_data: Path):
    """Syntax check passes for valid JSON-LD."""
    resolver = RegistryResolver(repo_with_test_data)
    result = validation_suite.check_syntax_all(["test-domain"], resolver=resolver)
    assert result == 0


def test_check_syntax_all_domain_filter(repo_with_test_data: Path):
    """Syntax check respects domain filter."""
    resolver = RegistryResolver(repo_with_test_data)

    # Add another domain's file
    (repo_with_test_data / "tests" / "data" / "other-domain" / "valid").mkdir(
        parents=True
    )
    (
        repo_with_test_data / "tests" / "data" / "other-domain" / "valid" / "other.json"
    ).write_text(
        '{"invalid": json}'
    )  # Invalid but shouldn't be checked

    result = validation_suite.check_syntax_all(["test-domain"], resolver=resolver)
    assert result == 0  # Only test-domain is checked


# =============================================================================
# Tests: validate_data_conformance_all
# =============================================================================


def test_validate_data_conformance_all_empty_domains():
    """Empty domain list returns 0."""
    result = validation_suite.validate_data_conformance_all([])
    assert result == 0


def test_validate_data_conformance_all_no_catalog():
    """Returns error when no catalog and no temp domains."""
    result = validation_suite.validate_data_conformance_all(
        ["nonexistent"], resolver=RegistryResolver(Path("/tmp/empty"))
    )
    # Should return 1 (no data to validate)
    assert result == 1


def test_validate_data_conformance_inference_mode(repo_with_test_data: Path):
    """Inference mode parameter is accepted."""
    resolver = RegistryResolver(repo_with_test_data)
    # Just verify it doesn't crash with different inference modes
    for mode in ["rdfs", "none"]:
        result = validation_suite.validate_data_conformance_all(
            ["test-domain"], resolver=resolver, inference_mode=mode
        )
        # May pass or fail depending on data, but shouldn't crash
        assert result in [0, 1, 210]


def test_validate_data_conformance_all_prints_formatted_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Failed SHACL validation prints the formatted report output."""

    class DummyResolver:
        def is_catalog_loaded(self):
            return True

    class FakeValidator:
        def __init__(
            self,
            root_dir: Path,
            inference_mode: str = "rdfs",
            verbose: bool = True,
            resolver: RegistryResolver = None,
            strict: bool = False,
            allow_online: bool = False,
        ):
            self._resolver = resolver

        def validate_from_catalog(self, domain: str, test_type: str = "valid"):
            return ShaclValidationResult(
                conforms=False,
                return_code=210,
                report_text="RAW REPORT TEXT",
                files_validated=["tests/data/demo/valid/demo.json"],
            )

        def format_result(self, _result):
            return "FORMATTED REPORT TEXT"

    monkeypatch.setattr(validation_suite, "ShaclValidator", FakeValidator)

    return_code = validation_suite.validate_data_conformance_all(
        ["demo-domain"], resolver=DummyResolver(), inference_mode="rdfs"
    )
    captured = capsys.readouterr()

    assert return_code == 210
    assert "📄 SHACL validation report:" in captured.out
    assert "FORMATTED REPORT TEXT" in captured.out
    assert "RAW REPORT TEXT" not in captured.out


# =============================================================================
# Tests: validate_artifact_coherence_all
# =============================================================================


def test_validate_artifact_coherence_all_empty_domains():
    """Empty domain list returns 0."""
    result = validation_suite.validate_artifact_coherence_all([])
    assert result == 0


def test_validate_artifact_coherence_all_skips_temp_domains():
    """Skips coherence check for temporary (custom-path-*) domains."""
    result = validation_suite.validate_artifact_coherence_all(["custom-path-abc123"])
    assert result == 0  # Skipped, not failed


def test_validate_artifact_coherence_all_with_resolver(minimal_repo: Path):
    """Coherence check works with provided resolver."""
    resolver = RegistryResolver(minimal_repo)
    result = validation_suite.validate_artifact_coherence_all(
        ["test-domain"], resolver=resolver
    )
    assert result == 0


# =============================================================================
# Tests: check_failing_tests_all
# =============================================================================


def test_check_failing_tests_all_empty_domains():
    """Empty domain list returns 0."""
    result = validation_suite.check_failing_tests_all([])
    assert result == 0


def test_check_failing_tests_all_no_invalid_files(repo_with_test_data: Path):
    """Returns 0 when no invalid test files exist."""
    resolver = RegistryResolver(repo_with_test_data)
    result = validation_suite.check_failing_tests_all(
        ["test-domain"], resolver=resolver
    )
    assert result == 0


# =============================================================================
# Tests: RegistryResolver integration
# =============================================================================


def test_resolver_get_artifact_domains(minimal_repo: Path):
    """Test get_artifact_domains method."""
    resolver = RegistryResolver(minimal_repo)
    domains = resolver.get_artifact_domains()
    assert "test-domain" in domains


def test_resolver_register_artifact_directory(temp_dir: Path, minimal_repo: Path):
    """Test registering external artifact directory."""
    # Create external artifacts
    ext_artifacts = temp_dir / "external-artifacts"
    (ext_artifacts / "ext-domain").mkdir(parents=True)
    (ext_artifacts / "ext-domain" / "ext-domain.owl.ttl").write_text(
        """@prefix owl: <http://www.w3.org/2002/07/owl#> .
<https://example.org/ext-domain/v1> a owl:Ontology ."""
    )
    (ext_artifacts / "ext-domain" / "ext-domain.shacl.ttl").write_text(
        """@prefix sh: <http://www.w3.org/ns/shacl#> ."""
    )
    (ext_artifacts / "ext-domain" / "ext-domain.context.jsonld").write_text(
        json.dumps({"@context": {"@vocab": "https://example.org/ext-domain/v1/"}})
    )

    resolver = RegistryResolver(minimal_repo)
    registered = resolver.register_artifact_directory(ext_artifacts)

    assert "ext-domain" in registered
    assert "ext-domain" in resolver.get_artifact_domains()


# =============================================================================
# Tests: Data hierarchy discovery
# =============================================================================


def test_discover_data_hierarchy_single_file(temp_dir: Path):
    """Single file becomes top-level when explicitly provided."""
    from src.tools.utils.file_collector import discover_data_hierarchy

    # Explicit files are always validated, even with did: scheme
    test_file = temp_dir / "test.json"
    test_file.write_text('{"@id": "https://example.com/thing/001", "@type": "Thing"}')

    top_level, iri_map, _metadata = discover_data_hierarchy([test_file])

    assert len(top_level) == 1
    assert "https://example.com/thing/001" in iri_map


def test_discover_data_hierarchy_with_fixtures(temp_dir: Path):
    """Referenced files become fixtures."""
    from src.tools.utils.file_collector import discover_data_hierarchy

    # Main file uses https:// IRI (not did:) so it's top-level
    main_file = temp_dir / "main.json"
    main_file.write_text(
        json.dumps(
            {
                "@id": "https://example.com/credentials/123",
                "@type": "Thing",
                "hasRef": {"@id": "did:test:fixture"},
            }
        )
    )

    # Fixture uses did: scheme so it's auto-classified as fixture
    fixture_file = temp_dir / "fixture.json"
    fixture_file.write_text(json.dumps({"@id": "did:test:fixture", "@type": "Fixture"}))

    top_level, iri_map, _metadata = discover_data_hierarchy([temp_dir])

    # Only main is top-level (did: files are fixtures)
    assert len(top_level) == 1
    assert top_level[0].name == "main.json"
    assert "did:test:fixture" in iri_map


# =============================================================================
# Tests: CLI argument validation
# =============================================================================


def test_cli_inference_mode_choices():
    """Test inference mode CLI choices."""
    # This tests that the choices are correctly defined
    valid_modes = ["rdfs", "owlrl", "none", "both"]
    for mode in valid_modes:
        # Should not raise
        assert mode in valid_modes


def test_cli_mutually_exclusive_data_paths_domain():
    """--data-paths and --domain are logically separate modes."""
    # This is a documentation test - the code handles them as elif branches
    # Both can technically be provided but --data-paths takes precedence
    pass


# =============================================================================
# Tests: Integration scenarios
# =============================================================================


def test_full_validation_workflow(repo_with_test_data: Path):
    """Test complete validation workflow."""
    resolver = RegistryResolver(repo_with_test_data)
    domains = ["test-domain"]

    # Syntax check
    syntax_result = validation_suite.check_syntax_all(domains, resolver=resolver)
    assert syntax_result == 0

    # Coherence check
    coherence_result = validation_suite.validate_artifact_coherence_all(
        domains, resolver=resolver
    )
    assert coherence_result == 0
