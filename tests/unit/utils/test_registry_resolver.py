#!/usr/bin/env python3
"""
Unit tests for omb.utils.registry_resolver catalog resolution.
"""

import json
import logging
from pathlib import Path

from omb.utils.registry_resolver import RegistryResolver


def _write_registry(root: Path, registry: dict) -> None:
    registry_path = root / "docs" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2))


def _write_imports_catalog(root: Path, content: str) -> None:
    catalog_path = root / "imports" / "catalog-v001.xml"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(content)


def _write_artifacts_catalog(root: Path, content: str) -> None:
    catalog_path = root / "artifacts" / "catalog-v001.xml"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(content)


def test_get_base_ontology_paths_from_imports_catalog(temp_dir):
    registry = {
        "version": "1.0.0",
        "ontologies": {},
    }
    _write_registry(temp_dir, registry)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
</catalog>
""",
    )

    catalog_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://example.org/rdf" uri="rdf/rdf.owl.ttl"/>
  <uri name="http://example.org/context" uri="cred/cred.context.jsonld"/>
  <uri name="http://example.org/shapes" uri="sh/sh.shacl.ttl"/>
</catalog>
"""
    _write_imports_catalog(temp_dir, catalog_content)

    resolver = RegistryResolver(temp_dir)
    assert resolver.get_base_ontology_paths() == ["imports/rdf/rdf.owl.ttl"]


def test_get_base_ontology_paths_no_catalog_returns_empty(temp_dir):
    registry = {
        "version": "1.0.0",
        "ontologies": {},
    }
    _write_registry(temp_dir, registry)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
</catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)
    assert resolver.get_base_ontology_paths() == []


def test_artifacts_catalog_drives_domain_resolution(temp_dir):
    registry = {
        "version": "1.0.0",
        "ontologies": {},
    }
    _write_registry(temp_dir, registry)

    artifacts_catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://example.org/demo/v1" uri="demo/demo.owl.ttl"/>
  <uri name="http://example.org/demo/v1/shapes" uri="demo/demo.shacl.ttl"/>
  <uri name="http://example.org/demo/v1/context" uri="demo/demo.context.jsonld"/>
  <uri name="http://example.org/other/v2" uri="other/other.owl.ttl"/>
</catalog>
"""
    _write_artifacts_catalog(temp_dir, artifacts_catalog)

    resolver = RegistryResolver(temp_dir)

    assert resolver.list_domains() == ["demo", "other"]
    assert resolver.get_ontology_path("demo") == "artifacts/demo/demo.owl.ttl"
    assert resolver.get_shacl_paths("demo") == ["artifacts/demo/demo.shacl.ttl"]
    assert resolver.get_context_path("demo") == "artifacts/demo/demo.context.jsonld"
    assert resolver.get_iri("demo") == "http://example.org/demo/v1"
    assert (
        resolver.resolve_type_to_domain("http://example.org/demo/v1/SomeClass")
        == "demo"
    )


def test_base_ontology_filtering_by_iris(temp_dir):
    registry = {
        "version": "1.0.0",
        "ontologies": {},
    }
    _write_registry(temp_dir, registry)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
</catalog>
""",
    )

    imports_catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://www.w3.org/2000/01/rdf-schema#" uri="rdfs/rdfs.owl.ttl"/>
  <uri name="http://www.w3.org/2001/XMLSchema#" uri="xsd/xsd.owl.ttl"/>
  <uri name="http://www.w3.org/2004/02/skos/core#" uri="skos/skos.owl.ttl"/>
</catalog>
"""
    _write_imports_catalog(temp_dir, imports_catalog)

    resolver = RegistryResolver(temp_dir)
    filtered = resolver.get_base_ontology_paths_for_iris(
        {
            "http://www.w3.org/2001/XMLSchema#string",
            "http://www.w3.org/2004/02/skos/core#note",
        }
    )

    assert filtered == ["imports/skos/skos.owl.ttl", "imports/xsd/xsd.owl.ttl"]


def test_base_ontology_filtering_normalizes_http_https(temp_dir):
    registry = {
        "version": "1.0.0",
        "ontologies": {},
    }
    _write_registry(temp_dir, registry)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
</catalog>
""",
    )

    imports_catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="https://schema.org/" uri="schema/schema.owl.ttl"/>
</catalog>
"""
    _write_imports_catalog(temp_dir, imports_catalog)

    resolver = RegistryResolver(temp_dir)
    filtered = resolver.get_base_ontology_paths_for_iris({"https://schema.org/name"})

    assert filtered == ["imports/schema/schema.owl.ttl"]


def test_get_all_cataloged_files_filters_by_domain(temp_dir):
    """Test that get_all_cataloged_files filters by domain."""
    registry = {"version": "1.0.0", "ontologies": {}}
    _write_registry(temp_dir, registry)

    # Create test catalog with multiple domains
    tests_dir = temp_dir / "tests"
    tests_dir.mkdir()
    catalog_path = tests_dir / "catalog-v001.xml"
    catalog_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="did:test:domain1:file1" uri="tests/data/domain1/file1.json" domain="domain1" test-type="valid" category="test-data"/>
  <uri name="did:test:domain1:file2" uri="tests/data/domain1/file2.json" domain="domain1" test-type="valid" category="test-data"/>
  <uri name="did:test:domain2:file1" uri="tests/data/domain2/file1.json" domain="domain2" test-type="valid" category="test-data"/>
</catalog>
"""
    )

    # Create actual files (relative to root_dir)
    (temp_dir / "tests" / "data" / "domain1").mkdir(parents=True)
    (temp_dir / "tests" / "data" / "domain2").mkdir(parents=True)
    (temp_dir / "tests" / "data" / "domain1" / "file1.json").write_text("{}")
    (temp_dir / "tests" / "data" / "domain1" / "file2.json").write_text("{}")
    (temp_dir / "tests" / "data" / "domain2" / "file1.json").write_text("{}")

    # Create artifacts catalog
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
</catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)

    # Without domain filter - get all files
    all_files = resolver.get_all_cataloged_files(extensions={".json"})
    assert len(all_files.get(".json", [])) == 3

    # With domain filter - get only domain1 files
    domain1_files = resolver.get_all_cataloged_files(
        extensions={".json"}, domains=["domain1"]
    )
    assert len(domain1_files.get(".json", [])) == 2
    assert all("domain1" in str(f) for f in domain1_files.get(".json", []))

    # With domain filter - get only domain2 files
    domain2_files = resolver.get_all_cataloged_files(
        extensions={".json"}, domains=["domain2"]
    )
    assert len(domain2_files.get(".json", [])) == 1
    assert all("domain2" in str(f) for f in domain2_files.get(".json", []))


def test_is_imported_namespace_matches_imports_catalog(temp_dir):
    """is_imported_namespace returns True for IRIs whose namespace is in the imports catalog."""
    registry = {"version": "1.0.0", "ontologies": {}}
    _write_registry(temp_dir, registry)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
""",
    )
    _write_imports_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://www.w3.org/2002/07/owl" uri="owl/owl.owl.ttl"/>
  <uri name="https://schema.org/" uri="schema/schema.owl.ttl"/>
</catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)

    # Matches via imports catalog
    assert resolver.is_imported_namespace("http://www.w3.org/2002/07/owl#Class")
    assert resolver.is_imported_namespace("https://schema.org/Person")
    # http/https normalization
    assert resolver.is_imported_namespace("https://schema.org/QuantitativeValue")
    # Not in imports catalog
    assert not resolver.is_imported_namespace("https://unknown.example.org/v1/Thing")


def test_register_artifact_directory_logs_invalid_context_warning(temp_dir, caplog):
    registry = {"version": "1.0.0", "ontologies": {}}
    _write_registry(temp_dir, registry)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
""",
    )

    ext_artifacts = temp_dir / "external-artifacts"
    bad_domain = ext_artifacts / "bad-domain"
    bad_domain.mkdir(parents=True)
    (bad_domain / "bad-domain.owl.ttl").write_text(
        """@prefix owl: <http://www.w3.org/2002/07/owl#> .
<https://example.org/bad-domain/v1> a owl:Ontology ."""
    )
    (bad_domain / "bad-domain.context.jsonld").write_text("{ invalid json }")

    caplog.set_level(logging.WARNING)
    resolver = RegistryResolver(temp_dir)

    registered = resolver.register_artifact_directory(ext_artifacts)

    assert "bad-domain" in registered
    assert any(
        "Could not extract IRI from context" in record.message
        for record in caplog.records
    )


def _minimal_resolver(root: Path) -> RegistryResolver:
    """A resolver over an otherwise empty repository, enough for temp domains."""
    _write_registry(root, {"version": "1.0.0", "ontologies": {}})
    _write_artifacts_catalog(
        root,
        """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
""",
    )
    return RegistryResolver(root)


def test_create_temporary_domain_classifies_by_paired_snapshot(temp_dir):
    """A ``.expected`` snapshot beside a file is what makes it a negative fixture.

    Both files below sit in the same directory, so any rule based on the directory's
    name would have to classify them identically. Only the snapshot distinguishes them.
    """
    resolver = _minimal_resolver(temp_dir)
    data_dir = temp_dir / "payloads"
    data_dir.mkdir()

    plain = data_dir / "plain.json"
    plain.write_text('{"@id": "did:test:plain"}')
    negative = data_dir / "negative.json"
    negative.write_text('{"@id": "did:test:negative"}')
    (data_dir / "negative.expected").write_text("recorded report")

    domain = resolver.create_temporary_domain([plain, negative])

    valid = [Path(p).name for p in resolver.get_test_files(domain, test_type="valid")]
    invalid = [
        Path(p).name for p in resolver.get_test_files(domain, test_type="invalid")
    ]
    assert valid == ["plain.json"]
    assert invalid == ["negative.json"]


def test_create_temporary_domain_ignores_an_invalid_directory_name(temp_dir):
    """A file under ``invalid/`` with no snapshot is ordinary data.

    This is the behaviour change: previously the directory name alone marked the file as
    a negative fixture, so conformance skipped it and - before the dispatch fix - nothing
    validated it at all. Now it is conformance-checked like any other data.
    """
    resolver = _minimal_resolver(temp_dir)
    invalid_dir = temp_dir / "invalid"
    invalid_dir.mkdir()
    unpaired = invalid_dir / "case.json"
    unpaired.write_text('{"@id": "did:test:case"}')

    domain = resolver.create_temporary_domain([unpaired])

    assert [
        Path(p).name for p in resolver.get_test_files(domain, test_type="valid")
    ] == ["case.json"]
    assert resolver.get_test_files(domain, test_type="invalid") == []


def test_create_temporary_domain_logs_the_pairing(temp_dir, caplog):
    """The log names both halves of the pair, so an accepted failure is traceable."""
    resolver = _minimal_resolver(temp_dir)
    negative = temp_dir / "case.json"
    negative.write_text('{"@id": "did:test:case"}')
    (temp_dir / "case.expected").write_text("recorded report")

    caplog.set_level(logging.INFO)
    resolver.create_temporary_domain([negative])

    assert any(
        "case.json" in record.message and "case.expected" in record.message
        for record in caplog.records
    ), "the pairing must be visible in the log, not inferred by the reader"
