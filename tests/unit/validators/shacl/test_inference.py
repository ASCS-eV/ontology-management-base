#!/usr/bin/env python3
"""
Unit tests for omb.validators.shacl.inference.
"""

import pytest
from rdflib import RDF, RDFS, BNode, Graph, Literal, Namespace

from omb.validators.shacl.inference import (
    apply_rdfs_inference,
    apply_rdfs_inference_sparql,
)


def test_apply_rdfs_inference_subclass_and_domain():
    ex = Namespace("http://example.org/")
    data = Graph()
    ont = Graph()

    data.add((ex.instance, ex.prop, ex.obj))
    data.add((ex.instance, RDF.type, ex.Sub))

    ont.add((ex.Sub, RDFS.subClassOf, ex.Super))
    ont.add((ex.prop, RDFS.domain, ex.DomainClass))

    combined, inferred = apply_rdfs_inference(data, ont)
    assert (ex.instance, RDF.type, ex.Super) in combined
    assert (ex.instance, RDF.type, ex.DomainClass) in combined
    assert inferred >= 1


def test_apply_rdfs_inference_range_types_blank_and_iri_not_literal():
    """rdfs:range entailment (RDF 1.1 Semantics rdfs3 / OWL 2 RL prp-rng).

    The range type must be entailed for every *resource* object — both IRIs and
    blank nodes — because blank nodes are valid RDF subjects. Literal objects must
    NOT be typed, since RDF forbids literals in subject position.
    """
    ex = Namespace("http://example.org/")
    data = Graph()
    ont = Graph()

    bnode = BNode()
    data.add((ex.s, ex.hasChild, bnode))  # blank-node object
    data.add((ex.s, ex.hasChild, ex.iriChild))  # IRI object
    data.add((ex.s, ex.hasLabel, Literal("x")))  # literal object

    ont.add((ex.hasChild, RDFS.range, ex.Child))
    ont.add((ex.hasLabel, RDFS.range, ex.LabelType))

    combined, _ = apply_rdfs_inference(data, ont)

    # Range entailment types both blank-node and IRI objects.
    assert (bnode, RDF.type, ex.Child) in combined
    assert (ex.iriChild, RDF.type, ex.Child) in combined
    # Literal objects are never typed (they cannot be RDF subjects).
    assert (Literal("x"), RDF.type, ex.LabelType) not in combined


EX = Namespace("http://example.org/")


def _chain_graphs():
    """A subclass chain deep enough that one round of rdfs9 cannot close it."""
    data = Graph()
    data.add((EX.x, RDF.type, EX.C0))
    ont = Graph()
    for i in range(6):
        ont.add((EX[f"C{i}"], RDFS.subClassOf, EX[f"C{i + 1}"]))
    return data, ont


def _subproperty_chain_graphs():
    data = Graph()
    data.add((EX.s, EX.p0, EX.o))
    ont = Graph()
    for i in range(5):
        ont.add((EX[f"p{i}"], RDFS.subPropertyOf, EX[f"p{i + 1}"]))
    return data, ont


def _cyclic_graphs():
    """Cycles must terminate, not loop until the iteration cap."""
    data = Graph()
    data.add((EX.x, RDF.type, EX.A))
    data.add((EX.s, EX.p, EX.o))
    ont = Graph()
    ont.add((EX.A, RDFS.subClassOf, EX.B))
    ont.add((EX.B, RDFS.subClassOf, EX.A))
    ont.add((EX.A, RDFS.subClassOf, EX.A))  # self-loop, excluded by the rule
    ont.add((EX.p, RDFS.subPropertyOf, EX.q))
    ont.add((EX.q, RDFS.subPropertyOf, EX.p))
    return data, ont


def _domain_range_interaction_graphs():
    """Domain output feeds the range pass through rdf:type's own range."""
    data = Graph()
    data.add((EX.s, EX.p, EX.o))
    data.add((EX.s, EX.lit, Literal("v")))
    data.add((EX.s, EX.anon, BNode("b1")))
    ont = Graph()
    ont.add((EX.p, RDFS.domain, EX.D))
    ont.add((EX.p, RDFS.range, EX.R))
    ont.add((EX.lit, RDFS.range, EX.NeverApplied))
    ont.add((EX.anon, RDFS.range, EX.AnonRange))
    ont.add((RDF.type, RDFS.range, RDFS.Class))
    ont.add((RDF.type, RDFS.domain, RDFS.Resource))
    return data, ont


def _schema_in_data_graphs():
    """Schema axioms asserted by the data, not the ontology."""
    data = Graph()
    data.add((EX.x, RDF.type, EX.Sub))
    data.add((EX.Sub, RDFS.subClassOf, EX.Super))
    data.add((EX.mine, RDFS.domain, EX.MineDomain))
    data.add((EX.x, EX.mine, EX.y))
    ont = Graph()
    ont.add((EX.Super, RDFS.subClassOf, EX.Top))
    return data, ont


def _derived_schema_graphs():
    """rdfs7 derives a subClassOf triple, which rdfs9 must then fire on."""
    data = Graph()
    data.add((EX.Sub, EX.narrower, EX.Super))
    data.add((EX.x, RDF.type, EX.Sub))
    ont = Graph()
    ont.add((EX.narrower, RDFS.subPropertyOf, RDFS.subClassOf))
    return data, ont


GRAPH_CASES = {
    "subclass_chain": _chain_graphs,
    "subproperty_chain": _subproperty_chain_graphs,
    "cycles": _cyclic_graphs,
    "domain_range_interaction": _domain_range_interaction_graphs,
    "schema_in_data": _schema_in_data_graphs,
    "derived_schema": _derived_schema_graphs,
}


@pytest.mark.parametrize("case", sorted(GRAPH_CASES))
@pytest.mark.parametrize("iterate_to_fixpoint", [True, False])
def test_indexed_engine_matches_the_sparql_rules(case, iterate_to_fixpoint):
    """The indexed engine must conclude exactly what the SPARQL rules conclude.

    The SPARQL strings in the module are the normative statement of the rules;
    the indexed evaluation is only a faster way to reach the same fixpoint. Any
    divergence here is a silent change to every SHACL verdict in the project,
    so it is checked triple for triple rather than by spot assertions.
    """
    data, ont = GRAPH_CASES[case]()

    indexed, indexed_count = apply_rdfs_inference(
        data, ont, iterate_to_fixpoint=iterate_to_fixpoint
    )
    reference, reference_count = apply_rdfs_inference_sparql(
        data, ont, iterate_to_fixpoint=iterate_to_fixpoint
    )

    assert set(indexed) == set(reference)
    assert indexed_count == reference_count


def test_indexed_engine_matches_the_sparql_rules_on_repository_artifacts(root_dir):
    """Same check against a real ontology and a real instance document.

    The synthetic cases above isolate individual rule interactions; this one
    exercises the rules against the shape of data the suite actually validates,
    where the ontology dwarfs the data and most conclusions are redundant.
    """
    ont = Graph()
    for artifact in sorted((root_dir / "artifacts" / "manifest").glob("*.ttl")):
        ont.parse(artifact, format="turtle")
    data = Graph()
    data.parse(
        root_dir / "tests" / "data" / "manifest" / "valid" / "manifest_instance.json",
        format="json-ld",
    )
    assert len(ont) > 0 and len(data) > 0

    indexed, indexed_count = apply_rdfs_inference(data, ont)
    reference, reference_count = apply_rdfs_inference_sparql(data, ont)

    assert set(indexed) == set(reference)
    assert indexed_count == reference_count


def test_apply_rdfs_inference_closes_a_chain_deeper_than_one_round():
    """Semi-naive rounds must still reach the end of a long subclass chain.

    The frontier shrinks to nothing only when the chain is exhausted; stopping
    a round early would leave the deepest superclasses unasserted, and SHACL
    would then miss every shape targeting them.
    """
    data, ont = _chain_graphs()
    combined, _ = apply_rdfs_inference(data, ont)

    for i in range(1, 7):
        assert (EX.x, RDF.type, EX[f"C{i}"]) in combined


def test_apply_rdfs_inference_terminates_on_cyclic_hierarchies():
    data, ont = _cyclic_graphs()
    combined, _ = apply_rdfs_inference(data, ont)

    assert (EX.x, RDF.type, EX.B) in combined
    assert (EX.s, EX.q, EX.o) in combined
    # The rules exclude the reflexive step, so no self-typing is introduced.
    assert (EX.A, RDFS.subClassOf, EX.A) in combined


def test_apply_rdfs_inference_reports_the_number_of_new_triples():
    """The reported count must be the number of triples actually added."""
    data, ont = _chain_graphs()
    before = set(data) | set(ont)

    combined, inferred = apply_rdfs_inference(data, ont)

    assert inferred == len(set(combined) - before)
