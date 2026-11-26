"""Tests for the IRI parsing in omb.utils.class_page_generator."""

import pytest
from rdflib import OWL, RDF, Graph, Literal, URIRef

from omb.utils.class_page_generator import (
    _extract_version_info,
    extract_domain_from_iri,
)


@pytest.mark.parametrize(
    ("iri", "domain"),
    [
        ("https://w3id.org/ascs-ev/envited-x/manifest/v5/Manifest", "manifest"),
        ("https://w3id.org/ascs-ev/envited-x/manifest/v5#Manifest", "manifest"),
        ("https://w3id.org/ascs-ev/envited-x/openlabel/v1.1.0-alpha/Tag", "openlabel"),
        ("https://w3id.org/gaia-x/development#Issuer", "gx"),
        ("https://example.org/no-version/Thing", None),
    ],
)
def test_extract_domain_from_iri(iri, domain):
    assert extract_domain_from_iri(iri) == domain


def _ontology(iri: str, version_info: str | None = None) -> Graph:
    g = Graph()
    g.add((URIRef(iri), RDF.type, OWL.Ontology))
    if version_info is not None:
        g.add((URIRef(iri), OWL.versionInfo, Literal(version_info)))
    return g


@pytest.mark.parametrize(
    ("iri", "version"),
    [
        ("https://w3id.org/ascs-ev/envited-x/hdmap/v6", "v6"),
        ("https://w3id.org/ascs-ev/envited-x/openlabel/v1.1.0-alpha", "v1.1.0-alpha"),
        ("https://example.org/unversioned", "unknown"),
    ],
)
def test_version_falls_back_to_the_ontology_iri(iri, version):
    """Without owl:versionInfo or pav:version the version comes from the IRI."""
    assert _extract_version_info(_ontology(iri)) == version


def test_version_info_wins_over_the_iri():
    g = _ontology("https://w3id.org/ascs-ev/envited-x/hdmap/v6", "6.1.0")
    assert _extract_version_info(g) == "v6.1.0"
