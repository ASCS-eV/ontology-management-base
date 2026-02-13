#!/usr/bin/env python3
"""
Unit tests for context_generator.py

Tests the JSON-LD context generation from OWL/SHACL artifacts.
"""

import json
from pathlib import Path

import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, XSD

from src.tools.utils.context_generator import (
    extract_ontology_iri,
    extract_prefix_from_iri,
    extract_property_datatypes,
    generate_context,
)

# Test namespace
SH = Namespace("http://www.w3.org/ns/shacl#")


class TestExtractPrefixFromIri:
    """Tests for extract_prefix_from_iri function."""

    def test_manifest_iri(self):
        """Should extract 'manifest' from manifest ontology IRI."""
        iri = "https://w3id.org/ascs-ev/envited-x/manifest/v5"
        assert extract_prefix_from_iri(iri) == "manifest"

    def test_hdmap_iri_with_trailing_slash(self):
        """Should extract 'hdmap' from hdmap ontology IRI with trailing slash."""
        iri = "https://w3id.org/ascs-ev/envited-x/hdmap/v5/"
        assert extract_prefix_from_iri(iri) == "hdmap"

    def test_legacy_gaia_x_iri(self):
        """Should extract domain from legacy gaia-x4plcaad IRI."""
        iri = "https://w3id.org/gaia-x4plcaad/ontologies/scenario/v5"
        assert extract_prefix_from_iri(iri) == "scenario"

    def test_simple_iri(self):
        """Should handle simple IRI without version pattern."""
        iri = "https://example.org/ontology/myterm"
        assert extract_prefix_from_iri(iri) == "myterm"


class TestExtractOntologyIri:
    """Tests for extract_ontology_iri function."""

    def test_extracts_ontology_iri(self):
        """Should extract ontology IRI from graph with owl:Ontology."""
        g = Graph()
        ont_iri = URIRef("https://example.org/ontology/v1")
        g.add((ont_iri, RDF.type, OWL.Ontology))

        result = extract_ontology_iri(g)
        assert result == str(ont_iri)

    def test_returns_none_for_empty_graph(self):
        """Should return None when no owl:Ontology found."""
        g = Graph()
        result = extract_ontology_iri(g)
        assert result is None


class TestExtractPropertyDatatypes:
    """Tests for extract_property_datatypes function."""

    def test_extracts_string_datatype(self):
        """Should extract property with xsd:string datatype."""
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

    def test_extracts_integer_datatype(self):
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

    def test_extracts_float_datatype(self):
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

    def test_extracts_anyuri_datatype(self):
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

    def test_extracts_object_property_with_nodeKind(self):
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

    def test_extracts_object_property_with_node(self):
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

    def test_ignores_properties_from_other_domains(self):
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


class TestGenerateContext:
    """Tests for generate_context function."""

    def test_generate_context_manifest(self):
        """Should generate a valid context for manifest domain."""
        # This test requires actual manifest files to exist
        manifest_owl = Path("artifacts/manifest/manifest.owl.ttl")
        if not manifest_owl.exists():
            pytest.skip("Manifest OWL file not found")

        result = generate_context("manifest")

        assert result is not None
        assert "@context" in result
        assert "comments" in result

        ctx = result["@context"]
        assert "manifest" in ctx
        assert "xsd" in ctx

        # Check some expected properties
        assert "filePath" in ctx or "manifest:filePath" in str(ctx)

    def test_generate_context_nonexistent_domain(self):
        """Should return None for non-existent domain."""
        result = generate_context("nonexistent_domain_xyz")
        assert result is None


class TestRoundTrip:
    """Tests for round-trip equivalence of verbose and compact instances."""

    def test_roundtrip_simple_instance(self):
        """Compact and verbose instances should produce isomorphic graphs."""
        from rdflib.compare import isomorphic

        # Create a simple verbose instance with native JSON types
        # Note: When xsd:integer is specified, @value should be an integer
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

        # Create equivalent compact instance with context coercion
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
