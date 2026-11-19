#!/usr/bin/env python3
"""Exercise generated LinkML artifacts with real RDF and SHACL consumers.

FEATURE SET: ontology metadata, nested constraints and intentional model gaps.
USAGE: pytest tests/integration/test_linkml_models.py
DEPENDENCIES: rdflib, pyshacl, pytest.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SH, XSD

from omb.utils.context_resolver import (
    build_context_url_map,
    load_jsonld_with_local_contexts,
)
from omb.utils.registry_resolver import RegistryResolver

ROOT = Path(__file__).resolve().parents[2]
M = Namespace("https://w3id.org/ascs-ev/envited-x/manifest/v6/")
E = Namespace("https://w3id.org/ascs-ev/envited-x/envited-x/v4/")
OSI = Namespace("https://w3id.org/ascs-ev/envited-x/ositrace/v7/")
G = Namespace("https://w3id.org/ascs-ev/envited-x/georeference/v6/")
HEADER = Namespace("https://w3id.org/ascs-ev/envited-x/ontology-header/v1/")
SDO = Namespace("https://schema.org/")


@pytest.fixture(scope="module")
def local_models():
    """Use the generated local domains; Gaia-X validation has its own suite."""
    shapes, ontology = Graph(), Graph()
    for domain in ("manifest", "georeference", "envited-x", "ositrace"):
        shapes.parse(ROOT / f"artifacts/{domain}/{domain}.shacl.ttl")
        ontology.parse(ROOT / f"artifacts/{domain}/{domain}.owl.ttl")
    return shapes, ontology


def conforms(data, models):
    """Validate a data graph against generated shapes and named individuals."""
    shapes, ontology = models
    return validate(data + ontology, shacl_graph=shapes, inference="none")[0]


@pytest.mark.parametrize(
    "domain", ["manifest", "georeference", "envited-x", "ositrace", "openlabel-tagging"]
)
def test_ontology_header_references_are_nodes(domain):
    graph = Graph().parse(ROOT / f"artifacts/{domain}/{domain}.owl.ttl")
    ontology = next(graph.subjects(RDF.type, OWL.Ontology))
    assert (
        str(graph.value(ontology, DCTERMS.license))
        == "https://www.eclipse.org/legal/epl-2.0/"
    )
    assert isinstance(graph.value(ontology, DCTERMS.license), Literal)
    # The ontology IRI is the version IRI; OWL 2 header structure is not restated.
    assert graph.value(ontology, OWL.versionIRI) is None
    predicates = []
    if domain != "openlabel-tagging":
        predicates += [
            DCTERMS.publisher,
            DCTERMS.references,
            OWL.priorVersion,
            DCTERMS.source,
        ]
        assert isinstance(graph.value(ontology, DCTERMS.creator), Literal)
        assert isinstance(graph.value(ontology, DCTERMS.conformsTo), Literal)
    for predicate in predicates:
        values = list(graph.objects(ontology, predicate))
        assert len(values) == 1
        assert isinstance(values[0], URIRef)
        # OWL 2 has owl:priorVersion built in as an annotation property (§5.5), so it
        # is not declared; every other header predicate is.
        declared = set() if predicate in OWL else {OWL.AnnotationProperty}
        assert set(graph.objects(predicate, RDF.type)) == declared


@pytest.mark.parametrize(
    "domain",
    [
        "ontology-header",
        "manifest",
        "georeference",
        "envited-x",
        "ositrace",
        "simulation-asset",
    ],
)
def test_ontology_header_conforms_to_the_profile(domain):
    """Each header follows the shared profile, which a domain imports and does not redefine."""
    graph = Graph().parse(ROOT / f"artifacts/{domain}/{domain}.owl.ttl")
    ontology = next(graph.subjects(RDF.type, OWL.Ontology))
    assert (ontology, RDF.type, HEADER.OntologyHeader) in graph
    if domain != "ontology-header":
        assert (ontology, OWL.imports, URIRef(str(HEADER).rstrip("/"))) in graph
        # OWL 2 DL wants the class of a class assertion declared (§5.8.1); a domain
        # declares the metaclass and states nothing else about it.
        assert set(graph.predicate_objects(HEADER.OntologyHeader)) == {
            (RDF.type, OWL.Class)
        }
    shapes = Graph().parse(ROOT / "artifacts/ontology-header/ontology-header.shacl.ttl")
    assert validate(graph, shacl_graph=shapes, inference="none")[0]


# The ontologies a generated domain imports, itself first; Gaia-X is not generated here.
IMPORT_CLOSURE = {
    "ontology-header": ["ontology-header"],
    "manifest": ["manifest", "ontology-header"],
    "georeference": ["georeference", "ontology-header"],
    "envited-x": ["envited-x", "manifest", "ontology-header", "gx"],
    "ositrace": [
        "ositrace",
        "envited-x",
        "georeference",
        "manifest",
        "ontology-header",
        "gx",
    ],
    "openlabel-tagging": ["openlabel-tagging"],
    "simulation-asset": ["simulation-asset", "ontology-header"],
}


@pytest.mark.parametrize("domain", sorted(IMPORT_CLOSURE))
def test_restrictions_are_on_declared_properties(domain):
    """OWL 2 DL wants every property of an axiom declared (§5.8.1): a restriction
    names a slot by the IRI it is declared with, also in a nested class expression."""
    graphs = [
        Graph().parse(ROOT / f"artifacts/{name}/{name}.owl.ttl")
        for name in IMPORT_CLOSURE[domain]
    ]
    # Only object and data properties can be restricted; an annotation property
    # carries no logical meaning (OWL 2 §10).
    declared = {
        subject
        for graph in graphs
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
        for subject in graph.subjects(RDF.type, kind)
    }
    restricted = set(graphs[0].objects(None, OWL.onProperty))
    assert restricted or domain == "ontology-header"
    missing = restricted - declared
    assert not missing, sorted(missing)


# OWL 2 DL declares no IRI as two kinds of property (§5.8.1). Header annotations
# and data properties share DCMI Terms (GAPS G26); the clashes are pinned, so a
# fix or a new clash shows.
GX = Namespace("https://w3id.org/gaia-x/development#")
HEADER_DCMI_TERMS = {
    DCTERMS.conformsTo,
    DCTERMS.identifier,
    DCTERMS.license,
    DCTERMS.title,
}
PROPERTY_KIND_CLASHES = {
    "envited-x": HEADER_DCMI_TERMS | {GX.location},
    "ositrace": HEADER_DCMI_TERMS | {GX.location},
    "simulation-asset": HEADER_DCMI_TERMS,
}


@pytest.mark.parametrize("domain", sorted(IMPORT_CLOSURE))
def test_property_kind_clashes_remain_the_documented_gap(domain):
    kinds = {}
    for name in IMPORT_CLOSURE[domain]:
        graph = Graph().parse(ROOT / f"artifacts/{name}/{name}.owl.ttl")
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
            for prop in graph.subjects(RDF.type, kind):
                kinds.setdefault(prop, set()).add(kind)
    clashes = {prop for prop, found in kinds.items() if len(found) > 1}
    assert clashes == PROPERTY_KIND_CLASHES.get(domain, set())


@pytest.mark.parametrize("domain", ["envited-x", "openlabel-tagging"])
def test_context_defines_schema_for_schema_org_https(domain):
    """Data writes schema.org terms as ``schema:``; the models declare ``sdo`` because
    linkml:types holds ``schema`` for http://schema.org/. The context defines both."""
    context = json.loads(
        (ROOT / f"artifacts/{domain}/{domain}.context.jsonld").read_text()
    )["@context"]
    assert context["schema"] == context["sdo"] == str(SDO)


@pytest.fixture(scope="module")
def manifest_data():
    resolver = RegistryResolver(ROOT)
    contexts = build_context_url_map(resolver, ROOT)
    path = ROOT / "tests/data/manifest/valid/manifest_instance.json"
    return Graph().parse(
        data=load_jsonld_with_local_contexts(path, contexts), format="json-ld"
    )


def test_manifest_jsonld_artifact_requires_metadata_but_self_reference_does_not(
    manifest_data, local_models
):
    assert conforms(manifest_data, local_models)
    for field in (
        M.iri,
        URIRef("http://www.w3.org/2004/02/skos/core#note"),
        URIRef("http://www.w3.org/ns/shacl#conformsTo"),
    ):
        data = Graph() + manifest_data
        artifact = next(
            s for s in data.subjects(field, None) if (None, M.hasArtifacts, s) in data
        )
        data.remove((artifact, field, None))
        assert not conforms(data, local_models), field


def test_manifest_license_category_is_checked_at_the_property(
    manifest_data, local_models
):
    data = Graph() + manifest_data
    license_link = next(data.objects(None, M.hasLicense))
    data.set((license_link, M.hasCategory, M.isMiscellaneous))
    assert not conforms(data, local_models)


def test_manifest_numeric_exclusive_bound_remains_a_documented_gap(local_models):
    data = Graph()
    node = URIRef("urn:test:dimensions")
    for predicate, value in [
        (RDF.type, M.Dimensions),
        (M.unit, Literal("metres")),
        (M.width, Literal(-1.0, datatype=XSD.float)),
        (M.height, Literal(0.0, datatype=XSD.float)),
    ]:
        data.add((node, predicate, value))
    assert conforms(data, local_models)


@pytest.mark.parametrize("field", [OSI.topic, OSI.messageType, OSI.osiVersion])
def test_mcap_channel_requires_every_field(field, local_models):
    data = Graph().parse(
        data="""
        @prefix o: <https://w3id.org/ascs-ev/envited-x/ositrace/v7/> .
        <urn:test:format> a o:Format; o:fileFormat "MCAP";
            o:hasChannel <urn:test:channel> .
        <urn:test:channel> a o:Channel; o:topic "sensor";
            o:messageType "SensorData"; o:osiVersion "3.6.0" .
    """,
        format="turtle",
    )
    assert conforms(data, local_models)
    data.remove((URIRef("urn:test:channel"), field, None))
    assert not conforms(data, local_models)


def test_geodetic_reference_requires_epsg_or_name(local_models):
    data = Graph().parse(
        data="""
        @prefix g: <https://w3id.org/ascs-ev/envited-x/georeference/v6/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        <urn:test:crs> a g:GeodeticReferenceSystem; g:hasOrigin <urn:test:origin>;
            g:codeEPSG 4326 .
        <urn:test:origin> a g:LatLonCoordinate; g:lat "1.0"^^xsd:float;
            g:lon "2.0"^^xsd:float .
    """,
        format="turtle",
    )
    assert conforms(data, local_models)
    data.remove((URIRef("urn:test:crs"), G.codeEPSG, None))
    assert not conforms(data, local_models)
    data.add((URIRef("urn:test:crs"), G.coordinateSystemName, Literal("WGS84")))
    assert conforms(data, local_models)


def test_openlabel_uses_published_schema_iris():
    owl = Graph().parse(ROOT / "artifacts/openlabel-tagging/openlabel-tagging.owl.ttl")
    shapes = Graph().parse(
        ROOT / "artifacts/openlabel-tagging/openlabel-tagging.shacl.ttl"
    )
    assert (SDO.QuantitativeValue, RDF.type, OWL.Class) in owl
    assert (None, SH.targetClass, SDO.QuantitativeValue) in shapes
    for field in (SDO.minValue, SDO.maxValue):
        assert (field, RDF.type, OWL.DatatypeProperty) in owl
        assert (None, SH.path, field) in shapes


@pytest.mark.skipif(
    os.name == "nt",
    reason="build_linkml_domain.sh is a bash script; on Windows `bash` may be WSL's, outside this environment",
)
def test_skipped_rule_leaves_existing_artifacts_untouched(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/build_linkml_domain.sh", scripts)
    schema = tmp_path / "linkml/probe"
    schema.mkdir(parents=True)
    (schema / "probe.yaml").write_text("""
 id: https://example.org/probe
 name: probe
 prefixes:
   ex: https://example.org/
   linkml: https://w3id.org/linkml/
 default_prefix: ex
 imports: [linkml:types]
 classes:
   Thing:
     attributes:
       value: {range: string}
     rules:
       - postconditions:
           slot_conditions:
             value: {required: true}
""")
    output = tmp_path / "output"
    output.mkdir()
    for suffix in ("owl.ttl", "shacl.ttl", "context.jsonld"):
        (output / f"probe.{suffix}").write_text("existing artifact\n")
    # The script takes the generators from PATH, as `uv run` provides them; here
    # they come from the environment that runs the tests.
    tools = str(Path(sys.executable).parent)
    result = subprocess.run(
        ["bash", str(scripts / "build_linkml_domain.sh"), "probe", str(output)],
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}"},
    )
    assert result.returncode != 0
    assert "skipped, because" in result.stderr
    assert all(path.read_text() == "existing artifact\n" for path in output.iterdir())
