#!/usr/bin/env python3
"""
Unit tests for omb.validators.shacl.inference.
"""

from rdflib import RDF, RDFS, BNode, Graph, Literal, Namespace

from omb.validators.shacl.inference import apply_rdfs_inference


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
