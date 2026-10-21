#!/usr/bin/env python3
"""
RDFS inference engine with index-driven, semi-naive rule application.

WHICH RDFS RULES THIS IMPLEMENTS:
=================================
Rule names are those of RDF 1.1 Semantics, section 9.2.1 (RDFS entailment
patterns). This is deliberately a *subset*: only the rules that materialize the
``rdf:type`` and property triples SHACL needs in order to evaluate
``sh:targetClass``, ``sh:class`` and ``sh:closed``.

  - rdfs2  ``?p rdfs:domain ?c . ?x ?p ?y``  =>  ``?x a ?c``
  - rdfs3  ``?p rdfs:range ?c . ?x ?p ?y``   =>  ``?y a ?c``
  - rdfs7  ``?p1 rdfs:subPropertyOf ?p2 . ?x ?p1 ?y``  =>  ``?x ?p2 ?y``
  - rdfs9  ``?c1 rdfs:subClassOf ?c2 . ?x a ?c1``      =>  ``?x a ?c2``

rdfs5 and rdfs11 (transitivity of ``rdfs:subPropertyOf`` / ``rdfs:subClassOf``)
are not applied as rules, but iterating rdfs7 and rdfs9 to a fixpoint yields
every ``rdf:type`` and property triple they would have produced: a chain
``c1 ⊑ c2 ⊑ c3`` types an instance of ``c1`` as ``c2`` in one round and as
``c3`` in the next. Only the transitive *schema* triples themselves are left
unmaterialized, and SHACL does not read them. This is why the hierarchy rules
iterate and the domain/range rules do not.

The axiomatic and "everything is a resource" rules (rdfs1, rdfs4a/b, rdfs6,
rdfs8, rdfs10, rdfs12, rdfs13) are NOT applied. They would add an
``rdf:type rdfs:Resource`` triple for every node in the graph without changing
any SHACL verdict. Callers who need a complete RDFS entailment regime should
use ``--inference-mode owlrl``, which hands inference to pySHACL/OWL-RL.

HOW IT EVALUATES THEM:
======================
  - Each rule is driven from the small set of schema triples that can fire it
    (``rdfs:subClassOf``/``subPropertyOf``/``domain``/``range``) and resolved
    through RDFLib's indexes, so a rule costs what its schema costs rather than
    what the graph costs
  - The fixpoint loop is semi-naive: after the first full round, each round
    only considers joins with at least one premise among the previous round's
    conclusions, instead of rederiving the whole closure every round
  - Nothing in the hot path calls ``len(graph)``. On the Oxigraph store that is
    a ``SELECT (COUNT(DISTINCT ...))`` full scan (``oxrdflib.store.__len__``),
    which on an ontology-sized graph cost more than all of the rules together
  - Stops as soon as a round concludes nothing new
"""

from typing import Iterable, Set, Tuple

from rdflib import RDF, RDFS, Graph, Literal
from rdflib.term import Node

from omb.core.constants import FAST_STORE
from omb.core.logging import get_logger

# Module logger
logger = get_logger(__name__)

# Maximum iterations to prevent infinite loops
MAX_ITERATIONS = 10

Triple = Tuple[Node, Node, Node]

# The rules below are also expressed as SPARQL updates. Those strings are the
# normative statement of what each rule means and what
# ``apply_rdfs_inference_sparql`` executes; the indexed functions in this module
# must agree with them triple for triple, which
# ``test_inference.py::test_indexed_engine_matches_the_sparql_rules`` checks
# against the repository's own artifacts.

# Transitive hierarchy rules (need iteration for fixpoint)
_SUBCLASS_RULES = [
    # Rule: rdfs:subClassOf (single step, iterated for transitivity)
    """
    INSERT { ?x a ?superClass }
    WHERE {
        ?x a ?class .
        ?class rdfs:subClassOf ?superClass .
        FILTER(?class != ?superClass)
    }
    """,
    # Rule: rdfs:subPropertyOf (single step, iterated for transitivity)
    """
    INSERT { ?subject ?superProperty ?object }
    WHERE {
        ?subject ?property ?object .
        ?property rdfs:subPropertyOf ?superProperty .
        FILTER(?property != ?superProperty)
    }
    """,
]

# Domain/range rules (single-pass, no iteration needed)
_DOMAIN_RANGE_RULES = [
    # Rule: rdfs:domain
    """
    INSERT { ?subject a ?class }
    WHERE {
        ?subject ?property ?object .
        ?property rdfs:domain ?class .
    }
    """,
    # Rule: rdfs:range — RDF 1.1 Semantics rule rdfs3 / OWL 2 RL rule prp-rng:
    #   { ?p rdfs:range ?c . ?x ?p ?y }  =>  { ?y a ?c }
    # The range type is entailed for ANY resource object. Only literals are
    # excluded, because RDF forbids literals in subject position (RDF 1.1
    # Semantics, "generalized RDF triple" note). Blank nodes ARE valid subjects
    # and ARE entailed — so the guard is !isLiteral, not isIRI. Using isIRI would
    # silently drop the type of every anonymous (blank-node) object, e.g. nested
    # JSON-LD objects that carry no @id.
    """
    INSERT { ?object a ?class }
    WHERE {
        ?subject ?property ?object .
        ?property rdfs:range ?class .
        FILTER(!isLiteral(?object))
    }
    """,
]

# Combined rule sets
RDFS_RULES_ITERATIVE = _SUBCLASS_RULES + _DOMAIN_RANGE_RULES
RDFS_RULES_SINGLE_PASS = _DOMAIN_RANGE_RULES


def _subclass_matches(graph: Graph) -> Iterable[Triple]:
    """``?x a ?c . ?c rdfs:subClassOf ?super`` => ``?x a ?super``.

    Driven from the subclass axioms rather than from the typed resources: an
    ontology states far fewer of them than a merged graph holds ``rdf:type``
    triples, and each one indexes straight to the resources it can type.
    """
    for klass, _, superclass in graph.triples((None, RDFS.subClassOf, None)):
        if klass == superclass:
            continue
        for resource in graph.subjects(RDF.type, klass):
            yield (resource, RDF.type, superclass)


def _subproperty_matches(graph: Graph) -> Iterable[Triple]:
    """``?s ?p ?o . ?p rdfs:subPropertyOf ?super`` => ``?s ?super ?o``."""
    for prop, _, superproperty in graph.triples((None, RDFS.subPropertyOf, None)):
        if prop == superproperty:
            continue
        for subject, _, obj in graph.triples((None, prop, None)):
            yield (subject, superproperty, obj)


def _domain_matches(graph: Graph) -> Iterable[Triple]:
    """``?s ?p ?o . ?p rdfs:domain ?c`` => ``?s a ?c``."""
    for prop, _, klass in graph.triples((None, RDFS.domain, None)):
        for subject in graph.subjects(prop, None):
            yield (subject, RDF.type, klass)


def _range_matches(graph: Graph) -> Iterable[Triple]:
    """``?s ?p ?o . ?p rdfs:range ?c`` => ``?o a ?c``, for non-literal ``?o``."""
    for prop, _, klass in graph.triples((None, RDFS.range, None)):
        for obj in graph.objects(None, prop):
            if not isinstance(obj, Literal):
                yield (obj, RDF.type, klass)


def _subclass_matches_delta(graph: Graph, delta: Set[Triple]) -> Iterable[Triple]:
    """rdfs9 restricted to joins with at least one premise in ``delta``.

    The two branches cover the two premise positions; each resolves its partner
    against the whole graph, so joins where *both* premises are new are found
    too. Everything else was already derived in an earlier round.
    """
    for subject, predicate, obj in delta:
        if predicate == RDF.type:
            for superclass in graph.objects(obj, RDFS.subClassOf):
                if obj != superclass:
                    yield (subject, RDF.type, superclass)
        elif predicate == RDFS.subClassOf and subject != obj:
            for resource in graph.subjects(RDF.type, subject):
                yield (resource, RDF.type, obj)


def _subproperty_matches_delta(graph: Graph, delta: Set[Triple]) -> Iterable[Triple]:
    """rdfs7 restricted to joins with at least one premise in ``delta``."""
    for subject, predicate, obj in delta:
        for superproperty in graph.objects(predicate, RDFS.subPropertyOf):
            if predicate != superproperty:
                yield (subject, superproperty, obj)
        if predicate == RDFS.subPropertyOf and subject != obj:
            for sub2, _, obj2 in graph.triples((None, subject, None)):
                yield (sub2, obj, obj2)


def _add_new(graph: Graph, derived: Iterable[Triple]) -> Set[Triple]:
    """Add the conclusions that are not in ``graph`` yet, and return them.

    Every solution is read before anything is written, so a rule never consumes
    its own conclusions — the same semantics as the SPARQL ``INSERT``/``WHERE``
    this replaces, and what makes the surrounding loop a fixpoint iteration
    rather than an unbounded cascade.

    Conclusions are collected into a set first, because a rule derives the same
    triple once per way of deriving it: ``rdfs:range`` alone reaches sixty
    thousand solutions covering about a thousand distinct triples.

    Which of them are new is decided by membership tests, never by comparing
    ``len(graph)`` before and after. On the Oxigraph store ``len()`` is a
    ``SELECT (COUNT(DISTINCT ...))`` full scan; asking it twice per rule cost
    more than every rule in this module put together. A membership test is an
    index probe, and the resulting set is what the next round needs anyway.
    """
    new: Set[Triple] = set()
    for triple in set(derived):
        if triple not in graph:
            graph.add(triple)
            new.add(triple)
    return new


def _apply_rule(graph: Graph, matches) -> int:
    """Apply a whole-graph rule to ``graph`` and report how many triples are new."""
    return len(_add_new(graph, matches(graph)))


def apply_rdfs_inference(
    data_graph: Graph,
    ontology_graph: Graph,
    iterate_to_fixpoint: bool = True,
    max_iterations: int = MAX_ITERATIONS,
) -> Tuple[Graph, int]:
    """
    Apply RDFS inference rules to data combined with ontology.

    See the module docstring for which RDFS rules this applies and why. The
    conclusions are those of the SPARQL formulation in this module, which
    ``apply_rdfs_inference_sparql`` still executes and the test suite compares
    against; only the evaluation strategy differs.

    Args:
        data_graph: Data graph to infer on
        ontology_graph: Ontology graph with class/property definitions
        iterate_to_fixpoint: If True, iterate rules until no new triples
        max_iterations: Maximum iterations to prevent infinite loops

    Returns:
        Tuple of (combined_graph, inferred_count)
    """
    # Create combined graph for inference
    combined = Graph(store=FAST_STORE)
    combined += data_graph
    combined += ontology_graph

    total_inferred = 0

    if iterate_to_fixpoint:
        # First round evaluates the hierarchy rules against the whole graph;
        # what it concludes becomes the frontier for the rounds after it.
        frontier = _add_new(combined, _subclass_matches(combined))
        frontier |= _add_new(combined, _subproperty_matches(combined))
        total_inferred += len(frontier)
        logger.debug("RDFS iteration 1: +%d triples", len(frontier))

        for iteration in range(1, max_iterations):
            if not frontier:
                logger.debug("RDFS fixpoint reached after %d iterations", iteration)
                break
            # Chained exactly as the whole-graph loop was: the subproperty rule
            # sees what the subclass rule just concluded, so the two engines
            # need the same number of rounds.
            new = _add_new(combined, _subclass_matches_delta(combined, frontier))
            new |= _add_new(
                combined, _subproperty_matches_delta(combined, frontier | new)
            )
            total_inferred += len(new)
            logger.debug("RDFS iteration %d: +%d triples", iteration + 1, len(new))
            frontier = new
        else:
            if frontier:
                logger.debug(
                    "RDFS inference stopped at the %d-iteration cap", max_iterations
                )

        # Apply domain/range rules once (they don't need iteration)
        total_inferred += _apply_rule(combined, _domain_matches)
        total_inferred += _apply_rule(combined, _range_matches)
    else:
        # Single-pass rules only (faster but incomplete for deep hierarchies)
        for matches in (
            _subclass_matches,
            _subproperty_matches,
            _domain_matches,
            _range_matches,
        ):
            total_inferred += _apply_rule(combined, matches)

    return combined, total_inferred


def apply_rdfs_inference_sparql(
    data_graph: Graph,
    ontology_graph: Graph,
    iterate_to_fixpoint: bool = True,
    max_iterations: int = MAX_ITERATIONS,
) -> Tuple[Graph, int]:
    """
    Apply the same RDFS rules as :func:`apply_rdfs_inference`, via SPARQL.

    Kept as the executable reading of the rule strings above: it is the
    reference the indexed engine is checked against, not a path validation
    takes. It is orders of magnitude slower on an ontology-sized graph, which
    is why it was replaced.

    Args:
        data_graph: Data graph to infer on
        ontology_graph: Ontology graph with class/property definitions
        iterate_to_fixpoint: If True, iterate rules until no new triples
        max_iterations: Maximum iterations to prevent infinite loops

    Returns:
        Tuple of (combined_graph, inferred_count)
    """
    # Create combined graph for inference
    combined = Graph(store=FAST_STORE)
    combined += data_graph
    combined += ontology_graph

    initial_count = len(combined)
    total_inferred = 0

    if iterate_to_fixpoint:
        # Iterative approach for transitive closure
        for iteration in range(max_iterations):
            count_before = len(combined)

            # Apply subClass and subProperty rules (need iteration)
            for rule in RDFS_RULES_ITERATIVE[:2]:
                try:
                    combined.update(rule)
                except Exception as e:
                    logger.debug("RDFS rule skipped: %s", e)

            count_after = len(combined)
            new_triples = count_after - count_before

            if new_triples == 0:
                logger.debug("RDFS fixpoint reached after %d iterations", iteration + 1)
                break

            logger.debug("RDFS iteration %d: +%d triples", iteration + 1, new_triples)

        # Apply domain/range rules once (they don't need iteration)
        for rule in RDFS_RULES_SINGLE_PASS:
            try:
                combined.update(rule)
            except Exception as e:
                logger.debug("RDFS rule skipped: %s", e)
    else:
        # Single-pass rules only (faster but incomplete for deep hierarchies)
        for rule in RDFS_RULES_ITERATIVE:
            try:
                combined.update(rule)
            except Exception as e:
                logger.debug("RDFS rule skipped: %s", e)

    total_inferred = len(combined) - initial_count

    return combined, total_inferred


def apply_rdfs_inference_transitive(
    data_graph: Graph,
    ontology_graph: Graph,
) -> Tuple[Graph, int]:
    """
    Apply RDFS inference using transitive closure operators.

    This is the original approach using rdfs:subClassOf+ which may be
    slower for deep hierarchies but is simpler to understand.

    Use apply_rdfs_inference() with iterate_to_fixpoint=True for better
    performance on larger ontologies.

    Args:
        data_graph: Data graph to infer on
        ontology_graph: Ontology graph with class/property definitions

    Returns:
        Tuple of (combined_graph, inferred_count)
    """
    combined = Graph(store=FAST_STORE)
    combined += data_graph
    combined += ontology_graph

    initial_count = len(combined)

    # Transitive closure rules
    transitive_rules = [
        """
        INSERT { ?x a ?superClass }
        WHERE {
            ?x a ?class .
            ?class rdfs:subClassOf+ ?superClass .
        }
        """,
        """
        INSERT { ?subject ?superProperty ?object }
        WHERE {
            ?subject ?property ?object .
            ?property rdfs:subPropertyOf+ ?superProperty .
        }
        """,
        """
        INSERT { ?subject a ?class }
        WHERE {
            ?subject ?property ?object .
            ?property rdfs:domain ?class .
        }
        """,
        # rdfs:range — same rule as _DOMAIN_RANGE_RULES above: !isLiteral (not
        # isIRI) so blank-node objects are typed too; see the spec-citation
        # comment on the canonical rule.
        """
        INSERT { ?object a ?class }
        WHERE {
            ?subject ?property ?object .
            ?property rdfs:range ?class .
            FILTER(!isLiteral(?object))
        }
        """,
    ]

    for rule in transitive_rules:
        try:
            combined.update(rule)
        except Exception as e:
            logger.debug("RDFS transitive rule skipped: %s", e)

    total_inferred = len(combined) - initial_count

    return combined, total_inferred
