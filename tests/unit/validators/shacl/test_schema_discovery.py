#!/usr/bin/env python3
"""
Unit tests for src.tools.validators.shacl.schema_discovery.
"""

import json
from pathlib import Path

from rdflib import RDF, Graph, Literal, URIRef

from src.tools.utils.registry_resolver import RegistryResolver
from src.tools.validators.shacl import schema_discovery


def _write_registry(root: Path) -> None:
    registry_path = root / "docs" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps({"version": "1.0.0", "ontologies": {}}))


def _write_artifacts_catalog(root: Path, content: str) -> None:
    catalog_path = root / "artifacts" / "catalog-v001.xml"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(content)


def _write_imports_catalog(root: Path, content: str) -> None:
    catalog_path = root / "imports" / "catalog-v001.xml"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(content)


def test_extract_rdf_types_predicates_and_datatypes():
    g = Graph()
    s = URIRef("http://example.org/s")
    t = URIRef("http://example.org/T")
    p = URIRef("http://example.org/p")
    g.add((s, RDF.type, t))
    g.add((s, p, Literal("x", datatype=URIRef("http://example.org/dt"))))

    assert schema_discovery.extract_rdf_types(g) == {str(t)}
    assert str(p) in schema_discovery.extract_predicates(g)
    assert "http://example.org/dt" in schema_discovery.extract_datatype_iris(g)


def test_discover_required_schemas_excludes_imported_namespace_types(temp_dir: Path):
    """Types from imported namespaces (imports catalog) are not flagged as unresolved."""
    _write_registry(temp_dir)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
""",
    )
    _write_imports_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://www.w3.org/1999/02/22-rdf-syntax-ns#" uri="rdf/rdf.owl.ttl"/>
  <uri name="http://www.w3.org/2000/01/rdf-schema#" uri="rdfs/rdfs.owl.ttl"/>
  <uri name="http://www.w3.org/2002/07/owl" uri="owl/owl.owl.ttl"/>
  <uri name="https://schema.org/" uri="schema/schema.owl.ttl"/>
</catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)
    _, _, unresolved = schema_discovery.discover_required_schemas(
        {
            "http://www.w3.org/2002/07/owl#Class",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
            "http://www.w3.org/2000/01/rdf-schema#Resource",
            "https://schema.org/QuantitativeValue",
        },
        resolver,
    )
    assert unresolved == set()


def test_discover_required_schemas_with_catalog(temp_dir: Path):
    _write_registry(temp_dir)
    artifacts_catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://example.org/demo/v1" uri="demo/demo.owl.ttl"/>
  <uri name="http://example.org/demo/v1/shapes" uri="demo/demo.shacl.ttl"/>
</catalog>
"""
    _write_artifacts_catalog(temp_dir, artifacts_catalog)

    resolver = RegistryResolver(temp_dir)
    ontology_paths, shacl_paths, unresolved = (
        schema_discovery.discover_required_schemas(
            {"http://example.org/demo/v1/Thing"}, resolver
        )
    )
    assert ontology_paths == ["artifacts/demo/demo.owl.ttl"]
    assert shacl_paths == ["artifacts/demo/demo.shacl.ttl"]
    assert unresolved == set()


def test_discover_required_schemas_uses_all_used_iris_for_artifacts(temp_dir: Path):
    _write_registry(temp_dir)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="http://example.org/demo/v1" uri="demo/demo.owl.ttl"/>
  <uri name="http://example.org/demo/v1/shapes" uri="demo/demo.shacl.ttl"/>
</catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)
    ontology_paths, shacl_paths, unresolved = (
        schema_discovery.discover_required_schemas(
            set(),
            resolver,
            used_iris={"http://example.org/demo/v1/hasThing"},
        )
    )

    assert ontology_paths == ["artifacts/demo/demo.owl.ttl"]
    assert shacl_paths == ["artifacts/demo/demo.shacl.ttl"]
    assert unresolved == set()


def test_discover_required_schemas_includes_import_shacl_for_used_iris(
    temp_dir: Path,
):
    _write_registry(temp_dir)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
""",
    )
    _write_imports_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <uri name="https://www.w3.org/ns/did#" uri="did/did.owl.ttl"/>
  <uri name="https://www.w3.org/ns/did#shapes" uri="did/did.shacl.ttl"/>
</catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)
    ontology_paths, shacl_paths, unresolved = (
        schema_discovery.discover_required_schemas(
            set(),
            resolver,
            used_iris={"https://www.w3.org/ns/did#serviceEndpoint"},
        )
    )

    assert ontology_paths == []
    assert shacl_paths == ["imports/did/did.shacl.ttl"]
    assert unresolved == set()


def test_discover_required_schemas_returns_unresolved_types(temp_dir: Path):
    """Types not matching any catalog domain are reported as unresolved."""
    _write_registry(temp_dir)
    _write_artifacts_catalog(
        temp_dir,
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
""",
    )

    resolver = RegistryResolver(temp_dir)
    _, _, unresolved = schema_discovery.discover_required_schemas(
        {"https://unknown.example.org/v1/MyClass"}, resolver
    )
    assert unresolved == {"https://unknown.example.org/v1/MyClass"}
