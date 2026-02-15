#!/usr/bin/env python3
"""
Unit tests for context_generator.py

Tests the JSON-LD context generation from OWL/SHACL artifacts.
"""

import json
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, XSD

from src.tools.core.iri_utils import iri_to_domain_hint
from src.tools.utils.context_generator import (
    _has_object_type_in_or_branches,
    extract_classes,
    extract_ontology_iri,
    extract_property_datatypes,
    generate_context,
)

# Test namespace
SH = Namespace("http://www.w3.org/ns/shacl#")

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
ARTIFACTS_DIR = ROOT_DIR / "artifacts"


class TestIriToDomainHint:
    """Tests for iri_to_domain_hint (replaces extract_prefix_from_iri)."""

    def test_iri_to_domain_hint_manifest_iri(self):
        """Should extract 'manifest' from manifest ontology IRI."""
        iri = "https://w3id.org/ascs-ev/envited-x/manifest/v5"
        assert iri_to_domain_hint(iri) == "manifest"

    def test_iri_to_domain_hint_trailing_slash(self):
        """Should extract 'hdmap' from hdmap ontology IRI with trailing slash."""
        iri = "https://w3id.org/ascs-ev/envited-x/hdmap/v5/"
        assert iri_to_domain_hint(iri) == "hdmap"

    def test_iri_to_domain_hint_legacy_iri(self):
        """Should extract domain from legacy gaia-x4plcaad IRI."""
        iri = "https://w3id.org/gaia-x4plcaad/ontologies/scenario/v5"
        assert iri_to_domain_hint(iri) == "scenario"

    def test_iri_to_domain_hint_simple_iri(self):
        """Should handle simple IRI without version pattern."""
        iri = "https://example.org/ontology/myterm"
        assert iri_to_domain_hint(iri) == "myterm"


class TestExtractOntologyIri:
    """Tests for extract_ontology_iri function."""

    def test_extract_ontology_iri_owl_graph_returns_iri(self):
        """Should extract ontology IRI from graph with owl:Ontology."""
        g = Graph()
        ont_iri = URIRef("https://example.org/ontology/v1")
        g.add((ont_iri, RDF.type, OWL.Ontology))

        result = extract_ontology_iri(g)
        assert result == str(ont_iri)

    def test_extract_ontology_iri_empty_graph_returns_none(self):
        """Should return None when no owl:Ontology found."""
        g = Graph()
        result = extract_ontology_iri(g)
        assert result is None


class TestExtractPropertyDatatypes:
    """Tests for extract_property_datatypes function."""

    def test_extract_property_datatypes_string_omits_type(self):
        """Should extract property with xsd:string datatype (no @type)."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(domain_iri + "myProperty")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.datatype, XSD.string))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "myProperty" in result
        assert result["myProperty"]["@id"] == "test:myProperty"
        # xsd:string should not have @type (it's the default)
        assert "@type" not in result["myProperty"]

    def test_extract_property_datatypes_integer_adds_type(self):
        """Should extract property with xsd:integer datatype and add @type."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(domain_iri + "count")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.datatype, XSD.integer))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "count" in result
        assert result["count"]["@id"] == "test:count"
        assert result["count"]["@type"] == "xsd:integer"

    def test_extract_property_datatypes_float_adds_type(self):
        """Should extract property with xsd:float datatype."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(domain_iri + "value")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.datatype, XSD.float))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "value" in result
        assert result["value"]["@type"] == "xsd:float"

    def test_extract_property_datatypes_anyuri_adds_type(self):
        """Should extract property with xsd:anyURI datatype."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(domain_iri + "filePath")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.datatype, XSD.anyURI))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "filePath" in result
        assert result["filePath"]["@type"] == "xsd:anyURI"

    def test_extract_property_datatypes_nodeKind_iri_returns_id(self):
        """Should detect object property via sh:nodeKind sh:IRI."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(domain_iri + "hasReference")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.nodeKind, SH.IRI))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "hasReference" in result
        assert result["hasReference"]["@type"] == "@id"

    def test_extract_property_datatypes_node_ref_returns_id(self):
        """Should detect object property via sh:node reference."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(domain_iri + "hasChild")
        child_shape = URIRef(domain_iri + "ChildShape")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.node, child_shape))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "hasChild" in result
        assert result["hasChild"]["@type"] == "@id"

    def test_extract_property_datatypes_other_domain_excluded(self):
        """Should not include properties from other namespaces."""
        g = Graph()
        domain_iri = "https://example.org/test/"
        other_iri = "https://other.org/ontology/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = URIRef(domain_iri + "prop_node_1")
        prop_path = URIRef(other_iri + "foreignProp")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))
        g.add((prop_node, SH.datatype, XSD.string))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "foreignProp" not in result

    def test_extract_property_datatypes_sh_or_with_node_returns_id(self):
        """Should detect object property via sh:or with sh:node branch."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = BNode()
        prop_path = URIRef(domain_iri + "hasResource")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))

        # Build sh:or list: ( [ sh:node ex:ShapeA ] [ sh:node ex:ShapeB ] )
        branch_a = BNode()
        branch_b = BNode()
        list_1 = BNode()
        list_2 = BNode()

        g.add((branch_a, SH.node, URIRef(domain_iri + "ShapeA")))
        g.add((branch_b, SH.node, URIRef(domain_iri + "ShapeB")))

        g.add((list_1, RDF.first, branch_a))
        g.add((list_1, RDF.rest, list_2))
        g.add((list_2, RDF.first, branch_b))
        g.add((list_2, RDF.rest, RDF.nil))

        g.add((prop_node, SH["or"], list_1))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "hasResource" in result
        assert result["hasResource"]["@type"] == "@id"

    def test_extract_property_datatypes_sh_or_with_and_node_returns_id(self):
        """Should detect object property via sh:or > sh:and > sh:node."""
        g = Graph()
        domain_iri = "https://example.org/test/"

        shape = URIRef(domain_iri + "TestShape")
        prop_node = BNode()
        prop_path = URIRef(domain_iri + "hasManifest")

        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.property, prop_node))
        g.add((prop_node, SH.path, prop_path))

        # Build sh:or ( [ sh:and ( [ sh:node ex:LinkShape ] ) ] )
        and_item = BNode()
        g.add((and_item, SH.node, URIRef(domain_iri + "LinkShape")))

        and_list = BNode()
        g.add((and_list, RDF.first, and_item))
        g.add((and_list, RDF.rest, RDF.nil))

        or_branch = BNode()
        g.add((or_branch, SH["and"], and_list))

        or_list = BNode()
        g.add((or_list, RDF.first, or_branch))
        g.add((or_list, RDF.rest, RDF.nil))

        g.add((prop_node, SH["or"], or_list))

        result = extract_property_datatypes(g, "test", domain_iri)

        assert "hasManifest" in result
        assert result["hasManifest"]["@type"] == "@id"


class TestExtractClasses:
    """Tests for extract_classes function."""

    def test_extract_classes_returns_local_names(self):
        """Should extract OWL class local names from domain namespace."""
        g = Graph()
        domain_iri = "https://example.org/test"

        g.add((URIRef(domain_iri + "/Foo"), RDF.type, OWL.Class))
        g.add((URIRef(domain_iri + "/Bar"), RDF.type, OWL.Class))
        g.add((URIRef("https://other.org/Baz"), RDF.type, OWL.Class))

        result = extract_classes(g, domain_iri)
        assert result == {"Foo", "Bar"}

    def test_extract_classes_ignores_other_namespace(self):
        """Should not include classes from other namespaces."""
        g = Graph()
        domain_iri = "https://example.org/test"

        g.add((URIRef("https://other.org/Baz"), RDF.type, OWL.Class))

        result = extract_classes(g, domain_iri)
        assert len(result) == 0


class TestHasObjectTypeInOrBranches:
    """Tests for _has_object_type_in_or_branches function."""

    def test_no_or_returns_false(self):
        """Should return False when no sh:or is present."""
        g = Graph()
        prop_node = BNode()
        assert _has_object_type_in_or_branches(g, prop_node) is False

    def test_or_with_node_returns_true(self):
        """Should return True when sh:or branch has sh:node."""
        g = Graph()
        prop_node = BNode()

        branch = BNode()
        g.add((branch, SH.node, URIRef("https://example.org/Shape")))

        list_node = BNode()
        g.add((list_node, RDF.first, branch))
        g.add((list_node, RDF.rest, RDF.nil))

        g.add((prop_node, SH["or"], list_node))

        assert _has_object_type_in_or_branches(g, prop_node) is True


class TestGenerateContext:
    """Tests for generate_context function."""

    def test_generate_context_manifest_returns_valid_context(self):
        """Should generate a valid context for manifest domain."""
        manifest_owl = ARTIFACTS_DIR / "manifest" / "manifest.owl.ttl"
        assert manifest_owl.exists(), "Manifest OWL file required for this test"

        result = generate_context("manifest")

        assert result is not None
        assert "@context" in result
        assert "comments" in result

        ctx = result["@context"]
        assert "manifest" in ctx
        assert "xsd" in ctx
        assert ctx.get("@version") == 1.1
        assert "filePath" in ctx

    def test_generate_context_nonexistent_domain_returns_none(self):
        """Should return None for non-existent domain."""
        result = generate_context("nonexistent_domain_xyz")
        assert result is None

    def test_generate_context_hdmap_has_or_properties_typed(self):
        """sh:or-based properties in hdmap should have @type: @id."""
        hdmap_owl = ARTIFACTS_DIR / "hdmap" / "hdmap.owl.ttl"
        if not hdmap_owl.exists():
            pytest.skip("hdmap OWL file not found")

        result = generate_context("hdmap")
        assert result is not None

        ctx = result["@context"]
        # These properties use sh:or with sh:node branches
        assert ctx.get("hasResourceDescription", {}).get("@type") == "@id"
        assert ctx.get("hasManifest", {}).get("@type") == "@id"


class TestRoundTrip:
    """Tests for round-trip equivalence of verbose and compact instances."""

    def test_roundtrip_verbose_compact_isomorphic(self):
        """Compact and verbose instances should produce isomorphic graphs."""
        from rdflib.compare import isomorphic

        verbose_instance = {
            "@context": {
                "test": "https://example.org/test/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
            },
            "@id": "test:instance1",
            "@type": "test:Thing",
            "test:count": {"@value": 42, "@type": "xsd:integer"},
            "test:name": "Test",
        }

        compact_instance = {
            "@context": {
                "test": "https://example.org/test/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "count": {"@id": "test:count", "@type": "xsd:integer"},
                "name": {"@id": "test:name"},
            },
            "@id": "test:instance1",
            "@type": "test:Thing",
            "count": 42,
            "name": "Test",
        }

        g_verbose = Graph()
        g_verbose.parse(data=json.dumps(verbose_instance), format="json-ld")

        g_compact = Graph()
        g_compact.parse(data=json.dumps(compact_instance), format="json-ld")

        assert isomorphic(g_verbose, g_compact), "Graphs should be isomorphic"
