#!/usr/bin/env python3
"""Exercise generated LinkML artifacts with real RDF and SHACL consumers.

FEATURE SET: ontology metadata, nested constraints and intentional model gaps.
USAGE: pytest tests/integration/test_linkml_models.py
DEPENDENCIES: rdflib, pyshacl, pytest.
"""

import os
import shutil
import subprocess
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
    "domain", ["manifest", "georeference", "envited-x", "ositrace", "openlabel-v2"]
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
    if domain != "openlabel-v2":
        predicates += [
            DCTERMS.publisher,
            DCTERMS.references,
            OWL.priorVersion,
            URIRef("http://www.w3.org/ns/prov#wasDerivedFrom"),
        ]
        assert isinstance(graph.value(ontology, DCTERMS.creator), Literal)
        assert isinstance(graph.value(ontology, DCTERMS.conformsTo), Literal)
    for predicate in predicates:
        values = list(graph.objects(ontology, predicate))
        assert len(values) == 1
        assert isinstance(values[0], URIRef)
        assert set(graph.objects(predicate, RDF.type)) == {OWL.AnnotationProperty}


@pytest.mark.parametrize(
    "domain", ["ontology-header", "manifest", "georeference", "envited-x", "ositrace"]
)
def test_ontology_header_conforms_to_the_profile(domain):
    """Each header follows the shared profile, which stays out of the domains."""
    graph = Graph().parse(ROOT / f"artifacts/{domain}/{domain}.owl.ttl")
    ontology = next(graph.subjects(RDF.type, OWL.Ontology))
    assert (ontology, RDF.type, HEADER.OntologyHeader) in graph
    if domain != "ontology-header":
        assert (ontology, OWL.imports, URIRef(str(HEADER).rstrip("/"))) in graph
        assert not set(graph.subjects(RDF.type, OWL.Class)) & {HEADER.OntologyHeader}
    shapes = Graph().parse(ROOT / "artifacts/ontology-header/ontology-header.shacl.ttl")
    assert validate(graph, shacl_graph=shapes, inference="none")[0]


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
    owl = Graph().parse(ROOT / "artifacts/openlabel-v2/openlabel-v2.owl.ttl")
    shapes = Graph().parse(ROOT / "artifacts/openlabel-v2/openlabel-v2.shacl.ttl")
    assert (SDO.QuantitativeValue, RDF.type, OWL.Class) in owl
    assert (None, SH.targetClass, SDO.QuantitativeValue) in shapes
    for field in (SDO.minValue, SDO.maxValue):
        assert (field, RDF.type, OWL.DatatypeProperty) in owl
        assert (None, SH.path, field) in shapes


@pytest.mark.skipif(
    os.name == "nt",
    reason="build_linkml_domain.sh is a POSIX script that runs the .venv/bin generators",
)
def test_skipped_rule_leaves_existing_artifacts_untouched(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/build_linkml_domain.sh", scripts)
    (tmp_path / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)
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
    result = subprocess.run(
        ["bash", str(scripts / "build_linkml_domain.sh"), "probe", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "skipped, because" in result.stderr
    assert all(path.read_text() == "existing artifact\n" for path in output.iterdir())
