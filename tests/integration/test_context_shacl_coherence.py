#!/usr/bin/env python3
"""
Regression tests: context @type coercions vs SHACL sh:datatype coherence.

These tests detect mismatches between JSON-LD context type coercions and
SHACL datatype constraints. For example, a context coercing a property to
``@id`` when the SHACL shape expects ``xsd:integer`` is a bug that allows
invalid data to slip through.

Also tests that JSON-LD type coercion only works with **term names**, not
compact IRIs (``prefix:name``), to prevent silent bypass of type checking.
"""

import json
from pathlib import Path

import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import SH, XSD

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

SH_NS = Namespace("http://www.w3.org/ns/shacl#")

# XSD numeric and boolean types that are incompatible with @id coercion
LITERAL_DATATYPES = {
    XSD.integer,
    XSD.nonNegativeInteger,
    XSD.positiveInteger,
    XSD.negativeInteger,
    XSD.nonPositiveInteger,
    XSD.float,
    XSD.double,
    XSD.decimal,
    XSD.boolean,
    XSD.dateTime,
    XSD.date,
    XSD.time,
    XSD.string,
    XSD.anyURI,
    XSD.language,
}


def _load_context_coercions(context_path: Path) -> dict[str, str]:
    """Extract property→type mappings from a context file.

    Returns a dict mapping term names to their coercion type IRI
    (e.g., ``{"length": "xsd:float", "hasContent": "@id"}``).
    """
    with open(context_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    ctx = doc.get("@context", {})
    if isinstance(ctx, list):
        for item in ctx:
            if isinstance(item, dict):
                ctx = item
                break
        else:
            return {}

    coercions: dict[str, str] = {}
    for key, val in ctx.items():
        if key.startswith("@"):
            continue
        if isinstance(val, dict) and "@type" in val:
            coercions[key] = val["@type"]
    return coercions


def _load_shacl_datatypes(shacl_path: Path) -> dict[str, URIRef]:
    """Extract property→sh:datatype mappings from a SHACL file.

    Returns a dict mapping property local name to the expected datatype
    (e.g., ``{"length": XSD.float}``).
    """
    g = Graph()
    g.parse(shacl_path, format="turtle")

    datatypes: dict[str, URIRef] = {}
    for prop_node in g.objects(predicate=SH.path):
        prop_str = str(prop_node)
        local_name = prop_str.rsplit("/", 1)[-1].rsplit("#", 1)[-1]

        # Find sh:datatype on shapes that reference this property
        for shape in g.subjects(predicate=SH.path, object=prop_node):
            for dt in g.objects(subject=shape, predicate=SH.datatype):
                datatypes[local_name] = URIRef(str(dt))

        # Also check inside sh:or lists for sh:datatype
        for shape in g.subjects(predicate=SH.path, object=prop_node):
            for or_list in g.objects(subject=shape, predicate=getattr(SH, "or")):
                _walk_rdf_list_for_datatypes(g, or_list, local_name, datatypes)

    return datatypes


def _walk_rdf_list_for_datatypes(
    g: Graph,
    list_node,
    local_name: str,
    datatypes: dict[str, URIRef],
) -> None:
    """Walk an RDF list to find sh:datatype constraints inside sh:or."""
    from rdflib.namespace import RDF

    current = list_node
    while current and current != RDF.nil:
        first_nodes = list(g.objects(subject=current, predicate=RDF.first))
        if first_nodes:
            first = first_nodes[0]
            for dt in g.objects(subject=first, predicate=SH.datatype):
                if local_name not in datatypes:
                    datatypes[local_name] = URIRef(str(dt))
        rest_nodes = list(g.objects(subject=current, predicate=RDF.rest))
        current = rest_nodes[0] if rest_nodes else None


def _resolve_coercion_to_uri(coercion: str, ctx: dict) -> str | None:
    """Resolve a context coercion value to a full URI string.

    Handles prefixed forms like ``xsd:float`` by expanding using the context.
    Returns ``None`` for ``@id`` and ``@vocab`` (IRI coercions).
    """
    if coercion in ("@id", "@vocab"):
        return None
    if coercion.startswith("http"):
        return coercion
    if ":" in coercion:
        prefix, local = coercion.split(":", 1)
        ns = ctx.get(prefix, "")
        if isinstance(ns, str):
            return ns + local
    return coercion


def _collect_domains() -> list[str]:
    """Collect domains that have both context and SHACL files."""
    domains = []
    for ctx_file in sorted(ARTIFACTS_DIR.glob("*/*.context.jsonld")):
        domain = ctx_file.parent.name
        shacl = ARTIFACTS_DIR / domain / f"{domain}.shacl.ttl"
        if shacl.exists():
            domains.append(domain)
    return domains

    # Domains with known @id coercion on literal properties.
    # These are LinkML-generated contexts where upstream gen-jsonld-context
    # collapses ``any_of`` with mixed literal/object ranges to ``@type: "@id"``.
    # See: https://github.com/linkml/linkml/issues/1483
    # Remove entries once the LinkML generator is fixed upstream.


KNOWN_ID_COERCION_ISSUES = {"gx"}

# Domains with known context/SHACL type mismatches.
# GX has overProvisioningRatio defined as both xsd:integer (CPU) and xsd:float
# (RAM) on different parent classes. The context picks one type while SHACL
# emits the other, creating a spurious mismatch. This is a GX schema issue.
KNOWN_TYPE_MISMATCHES: set[str] = {"gx"}


class TestContextShaclCoherence:
    """Verify that context type coercions are compatible with SHACL constraints."""

    @pytest.mark.parametrize("domain", _collect_domains())
    def test_no_id_coercion_on_literal_properties(self, domain):
        """Context must not use @id coercion for properties with SHACL literal datatypes.

        When a SHACL shape constrains a property with ``sh:datatype`` (a literal type),
        the corresponding context entry must NOT coerce to ``@id`` or ``@vocab``, because
        that would treat values as IRIs instead of typed literals.
        """
        if domain in KNOWN_ID_COERCION_ISSUES:
            pytest.xfail(
                f"Known issue: {domain} context has @id coercion on literal properties"
            )
        ctx_path = ARTIFACTS_DIR / domain / f"{domain}.context.jsonld"
        shacl_path = ARTIFACTS_DIR / domain / f"{domain}.shacl.ttl"

        coercions = _load_context_coercions(ctx_path)
        shacl_types = _load_shacl_datatypes(shacl_path)

        mismatches = []
        for prop, shacl_dt in shacl_types.items():
            if shacl_dt not in LITERAL_DATATYPES:
                continue
            ctx_coercion = coercions.get(prop)
            if ctx_coercion in ("@id", "@vocab"):
                mismatches.append(
                    f"  {prop}: context coerces to '{ctx_coercion}' "
                    f"but SHACL expects sh:datatype {shacl_dt}"
                )

        assert not mismatches, (
            f"Domain '{domain}' has @id/@vocab coercion on literal properties:\n"
            + "\n".join(mismatches)
        )

    @pytest.mark.parametrize("domain", _collect_domains())
    def test_coercion_datatype_matches_shacl(self, domain):
        """Context coercion type should be compatible with SHACL sh:datatype.

        For example, if SHACL expects ``xsd:float``, the context should coerce to
        ``xsd:float`` (or a compatible type), not to ``xsd:string``.
        """
        if domain in KNOWN_TYPE_MISMATCHES:
            pytest.xfail(
                f"Known issue: {domain} context has incompatible type coercions"
            )
        ctx_path = ARTIFACTS_DIR / domain / f"{domain}.context.jsonld"
        shacl_path = ARTIFACTS_DIR / domain / f"{domain}.shacl.ttl"

        with open(ctx_path, "r", encoding="utf-8") as f:
            ctx_doc = json.load(f)
        ctx = ctx_doc.get("@context", {})
        if isinstance(ctx, list):
            for item in ctx:
                if isinstance(item, dict):
                    ctx = item
                    break

        coercions = _load_context_coercions(ctx_path)
        shacl_types = _load_shacl_datatypes(shacl_path)

        # XSD type compatibility groups
        compatible_groups = [
            {
                str(XSD.integer),
                str(XSD.nonNegativeInteger),
                str(XSD.positiveInteger),
                str(XSD.negativeInteger),
                str(XSD.nonPositiveInteger),
            },
            {str(XSD.float), str(XSD.double), str(XSD.decimal)},
        ]

        def is_compatible(ctx_type_uri: str, shacl_type_uri: str) -> bool:
            if ctx_type_uri == shacl_type_uri:
                return True
            for group in compatible_groups:
                if ctx_type_uri in group and shacl_type_uri in group:
                    return True
            return False

        mismatches = []
        for prop, shacl_dt in shacl_types.items():
            ctx_coercion = coercions.get(prop)
            if not ctx_coercion or ctx_coercion in ("@id", "@vocab"):
                continue

            ctx_type_uri = _resolve_coercion_to_uri(ctx_coercion, ctx)
            if ctx_type_uri and not is_compatible(ctx_type_uri, str(shacl_dt)):
                mismatches.append(
                    f"  {prop}: context coerces to '{ctx_coercion}' ({ctx_type_uri}) "
                    f"but SHACL expects {shacl_dt}"
                )

        assert not mismatches, (
            f"Domain '{domain}' has incompatible context/SHACL types:\n"
            + "\n".join(mismatches)
        )


class TestCompactIriCoercionBypass:
    """Verify that compact IRIs bypass type coercion (regression detection)."""

    def test_compact_iri_does_not_coerce(self):
        """Using prefix:name instead of term name must not apply type coercion.

        This is a fundamental JSON-LD behavior: coercion is only applied to
        term names defined in the context, not to compact IRIs that happen
        to expand to the same IRI.
        """
        data_term_name = {
            "@context": {
                "ex": "http://example.org/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "value": {"@id": "ex:value", "@type": "xsd:float"},
            },
            "@id": "http://example.org/test",
            "value": "3.14",
        }

        data_compact_iri = {
            "@context": {
                "ex": "http://example.org/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "value": {"@id": "ex:value", "@type": "xsd:float"},
            },
            "@id": "http://example.org/test",
            "ex:value": "3.14",
        }

        g_term = Graph()
        g_term.parse(data=json.dumps(data_term_name), format="json-ld")

        g_compact = Graph()
        g_compact.parse(data=json.dumps(data_compact_iri), format="json-ld")

        prop = URIRef("http://example.org/value")

        # Term name: should have xsd:float datatype
        for _, _, o in g_term.triples((None, prop, None)):
            assert o.datatype == XSD.float, (
                f"Term name coercion should produce xsd:float, got {o.datatype}"
            )

        # Compact IRI: should NOT have xsd:float datatype (no coercion)
        for _, _, o in g_compact.triples((None, prop, None)):
            assert o.datatype != XSD.float, (
                f"Compact IRI should NOT apply coercion, "
                f"but got {o.datatype} — coercion was applied!"
            )
