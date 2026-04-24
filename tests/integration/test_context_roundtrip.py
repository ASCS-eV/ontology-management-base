#!/usr/bin/env python3
"""
Integration tests for JSON-LD context round-trip equivalence.

These tests verify that compact JSON-LD instances (using generated contexts)
produce equivalent RDF triples to verbose instances (explicit @value/@type).
"""

import json
from pathlib import Path

import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

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


def _is_linkml_domain(domain: str) -> bool:
    """Check if a domain has a LinkML schema (LinkML-managed)."""
    linkml_dir = ROOT_DIR / "linkml" / domain
    return (linkml_dir / f"{domain}.yaml").exists()


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

    def test_manifest_context_file_exists(self, manifest_context):
        """Context file should exist."""
        assert manifest_context.exists(), f"Context file not found: {manifest_context}"

    def test_instance_parses_with_inline_context(
        self, verbose_instance, manifest_context
    ):
        """Instance should parse successfully with inline context."""
        instance = load_context_inline(verbose_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Should have parsed some triples
        assert len(g) > 0, "Graph should contain triples"

    def test_instance_has_manifest_rdf_type(self, verbose_instance, manifest_context):
        """Instance should have correct RDF types after parsing."""
        instance = load_context_inline(verbose_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Check for expected type using proper RDF.type predicate
        manifest_type = "https://w3id.org/ascs-ev/envited-x/manifest/v5/Manifest"
        types = [str(o) for s, p, o in g.triples((None, RDF.type, None))]

        assert manifest_type in types, (
            f"Expected Manifest type not found. Found: {types}"
        )

    def test_datatype_coercion_integer_filesize(
        self, verbose_instance, manifest_context
    ):
        """Integer values should be correctly typed in RDF."""
        instance = load_context_inline(verbose_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Find fileSize triples
        file_size_uri = "https://w3id.org/ascs-ev/envited-x/manifest/v5/fileSize"
        xsd_integer = "http://www.w3.org/2001/XMLSchema#integer"

        for s, p, o in g:
            if str(p) == file_size_uri:
                assert str(o.datatype) == xsd_integer, (
                    f"fileSize should be xsd:integer, got {o.datatype}"
                )
                return

        # fileSize should exist in the graph
        pytest.fail("No fileSize triple found in graph")

    def test_datatype_coercion_float_width(self, verbose_instance, manifest_context):
        """Float values should be correctly typed in RDF."""
        instance = load_context_inline(verbose_instance, manifest_context)

        g = Graph()
        g.parse(data=json.dumps(instance), format="json-ld")

        # Find width triples
        width_uri = "https://w3id.org/ascs-ev/envited-x/manifest/v5/width"
        xsd_float = "http://www.w3.org/2001/XMLSchema#float"

        for s, p, o in g:
            if str(p) == width_uri:
                assert str(o.datatype) == xsd_float, (
                    f"width should be xsd:float, got {o.datatype}"
                )
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

        # LinkML-generated contexts don't include @version 1.1
        if not _is_linkml_domain(domain):
            assert ctx.get("@version") == 1.1, "Context should declare @version 1.1"

        # Should have standard prefixes
        assert "xsd" in ctx, "Context should define xsd prefix"
        # LinkML uses underscores in prefix names (e.g., openlabel_v2)
        domain_key = domain.replace("-", "_")
        assert (
            domain in ctx
            or domain_key in ctx
            or any(isinstance(v, str) and domain in v for v in ctx.values())
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
            assert domain_prefix_value.startswith("http"), (
                f"Prefix should be IRI: {domain_prefix_value}"
            )


def _build_context_url_map() -> dict:
    """Build context URL map using the real artifacts catalog."""
    from src.tools.utils.context_resolver import build_context_url_map
    from src.tools.utils.registry_resolver import RegistryResolver

    resolver = RegistryResolver(ROOT_DIR)
    return build_context_url_map(resolver, ROOT_DIR)


def _load_instance_with_local_contexts(instance_path: Path) -> Graph:
    """Load a JSON-LD instance with context URLs resolved to local files."""
    from src.tools.utils.context_resolver import load_jsonld_with_local_contexts

    url_map = _build_context_url_map()
    json_str = load_jsonld_with_local_contexts(instance_path, url_map)

    g = Graph()
    file_uri = instance_path.resolve().as_uri()
    g.parse(data=json_str, format="json-ld", base=file_uri, publicID=file_uri)
    return g


# Namespace IRIs used in assertions
GX_NS = "https://w3id.org/gaia-x/development#"
SCHEMA_NS = "https://schema.org/"
ENVITED_X_NS = "https://w3id.org/ascs-ev/envited-x/envited-x/v3/"
RESOURCE_DESC_ID = URIRef(
    "did:web:registry.envited-x.net::ResourceDescription:pX8mN4kL2vR9ZjW5bS7yH3cW1dGf6A8"
)


class TestEnvitedXBareNameContext:
    """Tests for envited-x instance using bare property names via gx context URL.

    Verifies that including the gx context URL in the @context array
    allows bare property names (no prefixes) in ResourceDescription,
    and that they resolve to the correct full IRIs.
    """

    INSTANCE_PATH = TESTS_DATA_DIR / "envited-x" / "valid" / "envited-x_instance.json"

    @pytest.fixture
    def graph(self) -> Graph:
        """Parse the envited-x instance into an RDF graph."""
        return _load_instance_with_local_contexts(self.INSTANCE_PATH)

    @pytest.fixture
    def instance_data(self) -> dict:
        """Load raw JSON of the envited-x instance."""
        with open(self.INSTANCE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # -- Context structure tests --

    def test_context_includes_gx_url(self, instance_data):
        """Instance @context array should include the gx context URL."""
        ctx = instance_data["@context"]
        assert isinstance(ctx, list), "@context should be an array"
        assert any(isinstance(entry, str) and "gaia-x" in entry for entry in ctx), (
            "gx context URL should be in @context array"
        )

    def test_context_neutralizes_vocab(self, instance_data):
        """Instance should have @vocab: null to prevent gx @vocab side effect."""
        ctx = instance_data["@context"]
        vocab_null_entries = [
            entry
            for entry in ctx
            if isinstance(entry, dict) and entry.get("@vocab") is None
        ]
        assert len(vocab_null_entries) == 1, (
            "@context should include {'@vocab': null} to neutralize gx @vocab"
        )

    # -- Property resolution tests (bare name → full IRI) --

    def test_bare_name_resolves_to_schema_name(self, graph):
        """Bare 'name' should resolve to schema:name."""
        predicate = URIRef(SCHEMA_NS + "name")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1, f"Expected 1 schema:name triple, found {len(triples)}"
        assert str(triples[0][2]) == "3D Model in Grafing"

    def test_bare_description_resolves_to_schema_description(self, graph):
        """Bare 'description' should resolve to schema:description."""
        predicate = URIRef(SCHEMA_NS + "description")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        assert "3D model" in str(triples[0][2])

    def test_bare_version_resolves_to_gx_version(self, graph):
        """Bare 'version' should resolve to gx:version."""
        predicate = URIRef(GX_NS + "version")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        assert str(triples[0][2]) == "1.0.0"

    def test_bare_license_resolves_to_gx_license(self, graph):
        """Bare 'license' should resolve to gx:license."""
        predicate = URIRef(GX_NS + "license")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        assert str(triples[0][2]) == "EPL-2.0"

    def test_bare_resource_policy_resolves_to_gx(self, graph):
        """Bare 'resourcePolicy' should resolve to gx:resourcePolicy."""
        predicate = URIRef(GX_NS + "resourcePolicy")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        assert str(triples[0][2]) == "allow"

    def test_bare_contains_pii_resolves_with_boolean_type(self, graph):
        """Bare 'containsPII' should resolve to gx:containsPII as xsd:boolean."""
        predicate = URIRef(GX_NS + "containsPII")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        obj = triples[0][2]
        assert isinstance(obj, Literal)
        assert obj.datatype == XSD.boolean, (
            f"containsPII should be xsd:boolean, got {obj.datatype}"
        )
        assert obj.toPython() is False

    def test_copyright_owned_by_resolves_to_gx_iri(self, graph):
        """Bare 'copyrightOwnedBy' with @id wrapper should resolve to gx IRI ref."""
        predicate = URIRef(GX_NS + "copyrightOwnedBy")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        obj = triples[0][2]
        assert isinstance(obj, URIRef), (
            f"copyrightOwnedBy should be a URI reference, got {type(obj).__name__}"
        )
        assert "LegalPerson" in str(obj)

    def test_produced_by_bare_string_resolves_to_gx_iri(self, graph):
        """Bare 'producedBy' as plain string should auto-coerce to @id via gx context."""
        predicate = URIRef(GX_NS + "producedBy")
        triples = list(graph.triples((RESOURCE_DESC_ID, predicate, None)))
        assert len(triples) == 1
        obj = triples[0][2]
        assert isinstance(obj, URIRef), (
            f"producedBy should be auto-coerced to URI reference by gx context "
            f"(@type: @id), got {type(obj).__name__}: {obj}"
        )
        assert "LegalPerson" in str(obj)

    # -- RDF type tests --

    def test_resource_description_has_correct_rdf_type(self, graph):
        """ResourceDescription node should have envited-x:ResourceDescription type."""
        expected_type = URIRef(ENVITED_X_NS + "ResourceDescription")
        types = list(graph.triples((RESOURCE_DESC_ID, RDF.type, None)))
        type_iris = [str(t[2]) for t in types]
        assert str(expected_type) in type_iris, (
            f"Expected ResourceDescription type not found. Found: {type_iris}"
        )

    # -- @vocab null safety test --

    def test_no_stray_gx_namespace_triples(self, graph):
        """With @vocab: null, undefined terms should NOT resolve to gx namespace.

        Checks that the only gx-namespaced predicates are the known ones
        from ResourceDescription. If @vocab leaked, random property names
        from other parts of the instance would also appear as gx: predicates.
        """
        known_gx_predicates = {
            URIRef(GX_NS + name)
            for name in [
                "version",
                "license",
                "resourcePolicy",
                "containsPII",
                "copyrightOwnedBy",
                "producedBy",
            ]
        }
        all_gx_predicates = {
            p for s, p, o in graph if str(p).startswith(GX_NS) and p != RDF.type
        }
        unexpected = all_gx_predicates - known_gx_predicates
        assert not unexpected, (
            f"Unexpected gx-namespaced predicates found (possible @vocab leak): "
            f"{[str(p) for p in unexpected]}"
        )

    # -- Instance uses bare names (no prefixes in JSON) --

    def test_instance_uses_bare_property_names(self, instance_data):
        """ResourceDescription properties should use bare names, not prefixed."""
        rd = instance_data["hasResourceDescription"]
        bare_props = [
            "name",
            "description",
            "version",
            "license",
            "resourcePolicy",
            "containsPII",
            "copyrightOwnedBy",
            "producedBy",
        ]
        for prop in bare_props:
            assert prop in rd, f"Expected bare property '{prop}' in ResourceDescription"

        # Should NOT have prefixed versions
        prefixed_props = [
            "schema:name",
            "schema:description",
            "gx:version",
            "gx:license",
            "gx:resourcePolicy",
            "gx:containsPII",
            "gx:copyrightOwnedBy",
            "gx:producedBy",
        ]
        for prop in prefixed_props:
            assert prop not in rd, (
                f"Prefixed property '{prop}' should be replaced with bare name"
            )
