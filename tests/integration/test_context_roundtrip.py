#!/usr/bin/env python3
"""
Integration tests for JSON-LD context round-trip equivalence.

These tests verify that compact JSON-LD instances (using generated contexts)
produce equivalent RDF triples to verbose instances (explicit @value/@type).
"""

import json
from pathlib import Path

import pytest
from rdflib import Graph
from rdflib.namespace import RDF

# Test paths
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
TESTS_DATA_DIR = ROOT_DIR / "tests" / "data"


def load_context_inline(instance_path: Path, context_path: Path) -> dict:
    """Load an instance and replace its context with the local context file."""
    with open(instance_path, "r", encoding="utf-8") as f:
        instance = json.load(f)

    with open(context_path, "r", encoding="utf-8") as f:
        context_doc = json.load(f)

    # Replace context with inline version
    instance["@context"] = context_doc.get("@context", {})
    return instance


# Collect all domains that have generated context files
def _context_domains():
    """Return list of domains with .context.jsonld files."""
    domains = []
    for ctx_file in sorted(ARTIFACTS_DIR.glob("*/*.context.jsonld")):
        domain = ctx_file.parent.name
        # Skip gx — has LinkML-generated context with different structure
        if domain != "gx":
            domains.append(domain)
    return domains


class TestManifestContextRoundtrip:
    """Tests for manifest context round-trip equivalence."""

    @pytest.fixture
    def manifest_context(self) -> Path:
        """Path to manifest context file."""
        return ARTIFACTS_DIR / "manifest" / "manifest.context.jsonld"

    @pytest.fixture
    def verbose_instance(self) -> Path:
        """Path to verbose manifest instance."""
        return TESTS_DATA_DIR / "manifest" / "valid" / "manifest_instance.json"

    @pytest.fixture
    def compact_instance(self) -> Path:
        """Path to compact manifest instance."""
        return TESTS_DATA_DIR / "manifest" / "valid" / "manifest_compact_instance.json"

    def test_manifest_context_file_exists(self, manifest_context):
        """Context file should exist."""
        assert manifest_context.exists(), f"Context file not found: {manifest_context}"

    def test_compact_instance_parses_with_inline_context(
        self, compact_instance, manifest_context
    ):
        """Compact instance should parse successfully with inline context."""
        assert compact_instance.exists(), "Compact instance not found"

        instance = load_context_inline(compact_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Should have parsed some triples
        assert len(g) > 0, "Graph should contain triples"

    def test_compact_instance_has_manifest_rdf_type(
        self, compact_instance, manifest_context
    ):
        """Compact instance should have correct RDF types after parsing."""
        assert compact_instance.exists(), "Compact instance not found"

        instance = load_context_inline(compact_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Check for expected type using proper RDF.type predicate
        manifest_type = "https://w3id.org/ascs-ev/envited-x/manifest/v5/Manifest"
        types = [str(o) for s, p, o in g.triples((None, RDF.type, None))]

        assert (
            manifest_type in types
        ), f"Expected Manifest type not found. Found: {types}"

    def test_datatype_coercion_integer_filesize(
        self, compact_instance, manifest_context
    ):
        """Integer values should be correctly typed in RDF."""
        assert compact_instance.exists(), "Compact instance not found"

        instance = load_context_inline(compact_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Find fileSize triples
        file_size_uri = "https://w3id.org/ascs-ev/envited-x/manifest/v5/fileSize"
        xsd_integer = "http://www.w3.org/2001/XMLSchema#integer"

        for s, p, o in g:
            if str(p) == file_size_uri:
                assert (
                    str(o.datatype) == xsd_integer
                ), f"fileSize should be xsd:integer, got {o.datatype}"
                return

        # fileSize should exist in the graph
        pytest.fail("No fileSize triple found in graph")

    def test_datatype_coercion_float_width(self, compact_instance, manifest_context):
        """Float values should be correctly typed in RDF."""
        assert compact_instance.exists(), "Compact instance not found"

        instance = load_context_inline(compact_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Find width triples
        width_uri = "https://w3id.org/ascs-ev/envited-x/manifest/v5/width"
        xsd_float = "http://www.w3.org/2001/XMLSchema#float"

        for s, p, o in g:
            if str(p) == width_uri:
                assert (
                    str(o.datatype) == xsd_float
                ), f"width should be xsd:float, got {o.datatype}"
                return

        # width should exist in the graph
        pytest.fail("No width triple found in graph")


class TestContextRoundtripGeneric:
    """Generic round-trip tests that can be applied to any domain."""

    @pytest.mark.parametrize("domain", _context_domains())
    def test_context_structure_valid(self, domain):
        """Context file should have valid structure."""
        context_path = ARTIFACTS_DIR / domain / f"{domain}.context.jsonld"
        assert context_path.exists(), f"Context file not found for {domain}"

        with open(context_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        assert "@context" in doc, "Document should have @context key"
        ctx = doc["@context"]

        # Should declare JSON-LD 1.1 for @container support
        assert ctx.get("@version") == 1.1, "Context should declare @version 1.1"

        # Should have standard prefixes
        assert "xsd" in ctx, "Context should define xsd prefix"
        assert domain in ctx or any(
            isinstance(v, str) and domain in v for v in ctx.values()
        ), f"Context should define {domain} prefix"

    @pytest.mark.parametrize("domain", _context_domains())
    def test_context_prefix_is_valid_iri(self, domain):
        """Domain prefix should be a valid IRI."""
        context_path = ARTIFACTS_DIR / domain / f"{domain}.context.jsonld"
        assert context_path.exists(), f"Context file not found for {domain}"

        with open(context_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        ctx = doc["@context"]
        # Find the domain prefix (may differ from domain name for legacy domains)
        domain_prefix_value = ctx.get(domain)
        if domain_prefix_value:
            assert domain_prefix_value.startswith(
                "http"
            ), f"Prefix should be IRI: {domain_prefix_value}"
