#!/usr/bin/env python3
"""Compare a candidate artifact set against the committed one for one domain.

Equivalence here is *observable behaviour*, not byte identity: a LinkML port
emits differently-shaped SHACL (different blank nodes, different
``sh:message`` text) that must still accept and reject exactly the same data.

Five layers, checked in order:

1. ``header``   - triples on the ``owl:Ontology`` node. A *missing* triple
                  fails (``registry_updater`` skips a domain whose
                  ``owl:versionInfo`` is missing); an *extra* one is advisory.
2. ``vocab``    - every committed ``owl:Class`` and named ``rdfs:subClassOf``
                  axiom must be present, and declared properties must be a
                  superset. Additions are advisory: the port is expected to
                  declare the datatype properties the hand-written OWL omits,
                  and LinkML renders enums as classes.
3. ``context``  - every test instance must expand to an isomorphic RDF graph
                  under the old and the new ``.context.jsonld``.
4. ``shacl``    - every test instance must get the same conformance verdict,
                  and each failing one the same set of
                  (resultPath, sourceConstraintComponent) pairs.
5. ``probe``    - adversarial instances derived from the committed shapes must
                  get the same verdict on both sides.

Deviations that are reviewed and accepted can be listed in
``linkml/<domain>/equivalence-exceptions.yaml``; anything else fails.

Usage::

    python scripts/compare_artifacts.py --domain ositrace \
        --candidate build/ositrace

Exit code is 0 only when every requested layer matches.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, URIRef  # noqa: E402

# Mutation probes deliberately carry malformed literals ("not-a-timestamp" typed
# xsd:dateTime). rdflib logs a full traceback for each one while still producing
# the ill-typed literal the probe needs, so hundreds of tracebacks would bury the
# report. The constraint violation is what the run is measuring, not the parse.
logging.getLogger("rdflib.term").setLevel(logging.CRITICAL)
from rdflib.compare import to_isomorphic  # noqa: E402
from rdflib.namespace import SH  # noqa: E402

LAYERS = ("header", "vocab", "context", "shacl", "probe")


# --------------------------------------------------------------------------
# shadow roots
# --------------------------------------------------------------------------
def build_shadow_root(
    repo_root: Path,
    domain: str,
    domain_dir: Path,
    workdir: Path,
    extra: Optional[Dict[str, Path]] = None,
) -> Path:
    """Mirror the repo with ``artifacts/<domain>/`` swapped for ``domain_dir``.

    ``extra`` swaps further domains the same way. A candidate whose shapes
    reference another *candidate* domain's terms (envited-x inherits
    ``manifest:LicenseLink`` from the LinkML manifest) must be measured with
    that dependency swapped too, or it is checked against terms that do not
    exist in the committed artifacts. Everything else is symlinked, so the
    catalogs keep resolving every other domain to the committed files.
    """
    swaps = {domain: domain_dir, **(extra or {})}
    root = workdir / domain_dir.name
    (root / "artifacts").mkdir(parents=True, exist_ok=True)

    for entry in (repo_root / "artifacts").iterdir():
        target = root / "artifacts" / entry.name
        if entry.name in swaps:
            continue
        if target.exists() or target.is_symlink():
            continue
        if entry.is_file():
            # catalog-v001.xml must be a real copy: its entries are relative, and
            # through a symlink they resolve against the *real* artifacts
            # directory, so the candidate's files would never be loaded.
            shutil.copy2(entry, target)
        else:
            target.symlink_to(entry)

    for name, source in swaps.items():
        swapped = root / "artifacts" / name
        if swapped.exists() or swapped.is_symlink():
            shutil.rmtree(swapped, ignore_errors=True)
        shutil.copytree(source, swapped)

    for name in ("imports", "tests", "docs"):
        src = repo_root / name
        dst = root / name
        if src.exists() and not dst.exists():
            dst.symlink_to(src)
    return root


# --------------------------------------------------------------------------
# layer 1 + 2: OWL
# --------------------------------------------------------------------------
def _ontology_node(graph: Graph) -> Optional[URIRef]:
    for subject in graph.subjects(RDF.type, OWL.Ontology):
        if not str(subject).endswith("/shapes"):
            return subject
    return None


def _freeze(graph: Graph, node) -> Set[Tuple[str, str]]:
    """Predicate/object pairs of ``node``, with blank-node objects summarised.

    A blank node is replaced by a sorted digest of its own predicate/object
    pairs, so structured contributors compare by content rather than by the
    blank-node label rdflib happened to mint.
    """
    out: Set[Tuple[str, str]] = set()
    for predicate, obj in graph.predicate_objects(node):
        if isinstance(obj, BNode):
            inner = sorted(f"{p}={o}" for p, o in graph.predicate_objects(obj))
            out.add((str(predicate), "bnode(" + "|".join(inner) + ")"))
        else:
            kind = "literal" if isinstance(obj, Literal) else "iri"
            lang = (
                f"@{obj.language}" if isinstance(obj, Literal) and obj.language else ""
            )
            out.add((str(predicate), f"{kind}:{obj}{lang}"))
    return out


def compare_header(base_owl: Graph, cand_owl: Graph, advisory: List[str]) -> List[str]:
    problems: List[str] = []
    base_node, cand_node = _ontology_node(base_owl), _ontology_node(cand_owl)
    if base_node is None or cand_node is None:
        return ["no owl:Ontology node found in one of the graphs"]
    if str(base_node) != str(cand_node):
        problems.append(f"ontology IRI: {base_node} -> {cand_node}")

    base_pairs, cand_pairs = _freeze(base_owl, base_node), _freeze(cand_owl, cand_node)
    for predicate, value in sorted(base_pairs - cand_pairs):
        problems.append(f"header MISSING  {predicate} {value}")
    # A missing header triple breaks consumers - registry_updater skips a domain
    # with no owl:versionInfo. An extra one cannot. Same asymmetry as the vocab
    # layer applies to classes and properties.
    extra = cand_pairs - base_pairs
    if extra:
        advisory.append(
            f"{len(extra)} additional header triple(s): "
            + ", ".join(
                sorted(p.rsplit("/", 1)[-1].rsplit("#", 1)[-1] for p, _ in extra)
            )
        )
    return problems


def _declared_properties(graph: Graph) -> Set[str]:
    kinds = (
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
        RDF.Property,
    )
    out: Set[str] = set()
    for kind in kinds:
        out |= {str(s) for s in graph.subjects(RDF.type, kind)}
    return out


def unexpanded_iris(*graphs: Graph) -> Dict[str, int]:
    """IRIs that are not absolute - an unexpanded CURIE such as ``<xsd:float>``.

    Such a term parses as a relative IRI and matches nothing, so a shape using
    it as ``sh:datatype`` or ``sh:path`` silently rejects every value. No layer
    comparing against the committed artifacts sees that directly.
    """
    import re

    absolute = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:(//|[^/].*)")
    known = ("http:", "https:", "urn:", "did:", "mailto:", "file:")
    counts: Dict[str, int] = defaultdict(int)
    for graph in graphs:
        for triple in graph:
            for term in triple:
                if isinstance(term, URIRef):
                    value = str(term)
                    if not value.startswith(known) or not absolute.match(value):
                        counts[value] += 1
    return dict(counts)


def compare_vocab(
    base_owl: Graph, cand_owl: Graph, namespace: str, advisory: List[str]
) -> List[str]:
    problems: List[str] = []

    base_classes = {
        str(c)
        for c in base_owl.subjects(RDF.type, OWL.Class)
        if str(c).startswith(namespace)
    }
    cand_classes = {
        str(c)
        for c in cand_owl.subjects(RDF.type, OWL.Class)
        if str(c).startswith(namespace)
    }
    for cls in sorted(base_classes - cand_classes):
        problems.append(f"class MISSING   {cls}")
    # Extra classes are additive (LinkML renders enums as classes) and cannot
    # break an existing consumer, so they are counted but not held against the
    # candidate - the same rule already applied to extra properties.
    extra_classes = cand_classes - base_classes
    if extra_classes:
        advisory.append(
            f"{len(extra_classes)} additional class(es), e.g. "
            + ", ".join(sorted(extra_classes)[:3])
        )

    base_props = {p for p in _declared_properties(base_owl) if p.startswith(namespace)}
    cand_props = {p for p in _declared_properties(cand_owl) if p.startswith(namespace)}
    # Superset, not equality: closing the undeclared-property gap is the point.
    for prop in sorted(base_props - cand_props):
        problems.append(f"property MISSING {prop}")

    def named_superclasses(graph: Graph) -> Set[Tuple[str, str]]:
        return {
            (str(s), str(o))
            for s, o in graph.subject_objects(RDFS.subClassOf)
            if isinstance(o, URIRef) and str(s).startswith(namespace)
        }

    base_sub, cand_sub = named_superclasses(base_owl), named_superclasses(cand_owl)
    for sub, sup in sorted(base_sub - cand_sub):
        problems.append(f"subClassOf MISSING {sub} -> {sup}")
    extra_sub = cand_sub - base_sub
    if extra_sub:
        advisory.append(f"{len(extra_sub)} additional subClassOf axiom(s)")
    return problems


# --------------------------------------------------------------------------
# layer 3: JSON-LD context
# --------------------------------------------------------------------------
def _grounded(graph: Graph) -> Set[Tuple[str, str, str, str]]:
    """Grounded statements: predicate, lexical value, datatype and language.

    Datatype is part of the signature because that is exactly where a context
    difference shows up - the same string carried as ``xsd:anyURI`` or as a
    plain literal is not the same statement.
    """
    return {
        (
            str(p),
            str(o),
            str(getattr(o, "datatype", "") or ""),
            str(getattr(o, "language", "") or ""),
        )
        for _, p, o in graph
        if not isinstance(o, BNode)
    }


def _prefix_block(*contexts: dict) -> dict:
    """Union of the namespace declarations across the given contexts.

    Each side declares a different prefix set - the hand-written context knows
    ``schema:``, the generated one knows ``manifest:`` - so comparing them in
    isolation reports prefix availability rather than term mapping. Giving both
    sides the same prefixes isolates what is actually under test.
    """
    merged: dict = {}
    for context in contexts:
        for key, value in context.items():
            if key.startswith("@") or not isinstance(value, str):
                continue
            if value.endswith("/") or value.endswith("#"):
                merged[key] = value
    return merged


def _expand_with_context(instance: Path, context_file: Path, shared: dict) -> Graph:
    """Expand ``instance`` forcing ``context_file`` as the only domain context.

    The instance's own remote ``@context`` URLs are dropped so the comparison
    isolates the candidate context rather than re-testing the catalogs; the
    trailing ``{"@vocab": None}`` mirrors what every instance in this repository
    does to stop unmapped terms leaking.
    """
    doc = json.loads(instance.read_text(encoding="utf-8"))
    context = json.loads(context_file.read_text(encoding="utf-8"))["@context"]
    doc["@context"] = [shared, context, {"@vocab": None}]
    graph = Graph()
    graph.parse(data=json.dumps(doc), format="json-ld")
    return graph


def compare_context(
    base_ctx: Path,
    cand_ctx: Path,
    instances: Sequence[Path],
    allowed_terms: Set[str],
    accepted: List[str],
) -> List[str]:
    problems: List[str] = []
    base_terms = json.loads(base_ctx.read_text(encoding="utf-8"))["@context"]
    cand_terms = json.loads(cand_ctx.read_text(encoding="utf-8"))["@context"]

    def term_map(raw: dict) -> Dict[str, str]:
        """Term -> absolute IRI, resolving CURIEs and ``@vocab``-relative ids.

        ``gen-jsonld-context`` writes ``{"@id": "Channel"}`` and leans on
        ``@vocab``; the hand-written context writes ``ositrace:Channel``. Both
        must be reduced to the same absolute IRI before they can be compared.
        """
        vocab = raw.get("@vocab") or ""
        prefixes = {
            k: v
            for k, v in raw.items()
            if isinstance(v, str)
            and not k.startswith("@")
            and (v.endswith("/") or v.endswith("#"))
        }

        def absolute(value: str) -> str:
            if value.startswith("http://") or value.startswith("https://"):
                return value
            prefix, sep, local = value.partition(":")
            if sep and prefix in prefixes:
                return prefixes[prefix] + local
            return vocab + value if vocab else value

        out: Dict[str, str] = {}
        for term, value in raw.items():
            if term.startswith("@") or term in prefixes:
                continue
            if isinstance(value, str):
                out[term] = absolute(value)
            elif isinstance(value, dict) and "@id" in value:
                out[term] = absolute(value["@id"])
        return out

    base_map, cand_map = term_map(base_terms), term_map(cand_terms)
    for term in sorted(set(base_map) - set(cand_map)):
        problems.append(f"term MISSING    {term} (was {base_map[term]})")
    for term in sorted(set(base_map) & set(cand_map)):
        if base_map[term] != cand_map[term]:
            problems.append(
                f"term REMAPPED   {term}: {base_map[term]} -> {cand_map[term]}"
            )
    allowed_terms = {base_map.get(t, t) for t in allowed_terms} | allowed_terms

    shared = _prefix_block(base_terms, cand_terms)
    for instance in instances:
        try:
            base_graph = _expand_with_context(instance, base_ctx, shared)
            cand_graph = _expand_with_context(instance, cand_ctx, shared)
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            problems.append(f"expand FAILED   {instance.name}: {exc}")
            continue
        if to_isomorphic(base_graph) != to_isomorphic(cand_graph):
            # Two independent parses mint different blank-node labels, so diff
            # on grounded statements (predicate + object value + datatype +
            # language) rather than raw triples, and attribute each difference
            # to the predicate so it can be matched against an exception.
            only_base = _grounded(base_graph) - _grounded(cand_graph)
            only_cand = _grounded(cand_graph) - _grounded(base_graph)
            culprits = {p for p, *_ in only_base} | {p for p, *_ in only_cand}
            unexplained = culprits - allowed_terms
            if not culprits:
                problems.append(
                    f"expand DIFFERS  {instance.name} (blank-node structure only)"
                )
                continue
            if not unexplained:
                accepted.append(
                    f"{instance.name}: "
                    + ", ".join(sorted(c.rsplit("/", 1)[-1] for c in culprits))
                )
                continue
            problems.append(f"expand DIFFERS  {instance.name}")
            for statement in sorted(only_base)[:6]:
                if statement[0] in unexplained:
                    problems.append(f"    only baseline:  {statement}")
            for statement in sorted(only_cand)[:6]:
                if statement[0] in unexplained:
                    problems.append(f"    only candidate: {statement}")
    return problems


# --------------------------------------------------------------------------
# layer 4: SHACL behaviour
# --------------------------------------------------------------------------
def _violation_signature(result) -> Set[Tuple[str, str, str]]:
    """(focusNode, resultPath, sourceConstraintComponent) triples from a report.

    IRI focus nodes are kept - they are stable across loads - and blank ones
    reduced to ``_``, since every parse mints new labels. ``sh:resultMessage``
    is ignored: LinkML's ``--message-template`` rewords every message, which is
    accepted churn.
    """
    graph = result.report_graph
    if graph is None:
        return set()
    out: Set[Tuple[str, str, str]] = set()
    for node in graph.objects(None, SH.result):
        focus = graph.value(node, SH.focusNode)
        path = graph.value(node, SH.resultPath)
        component = graph.value(node, SH.sourceConstraintComponent)
        out.add(
            (
                str(focus) if isinstance(focus, URIRef) else "_",
                str(path) if path else "-",
                str(component) if component else "-",
            )
        )
    return out


def run_validation(root: Path, files: Sequence[Path]) -> Dict[str, dict]:
    from omb.validators.shacl.validator import ShaclValidator

    validator = ShaclValidator(
        root_dir=root, inference_mode="rdfs", verbose=False, allow_online=False
    )
    results = validator.validate_each(list(files))
    out: Dict[str, dict] = {}
    for path, result in zip(files, results):
        out[path.name] = {
            "conforms": result.conforms,
            "violations": _violation_signature(result),
        }
    return out


def compare_shacl(
    base_root: Path,
    cand_root: Path,
    files: Sequence[Path],
    allowed_constraints: Set[str],
    accepted: List[str],
) -> List[str]:
    problems: List[str] = []
    base = run_validation(base_root, files)
    cand = run_validation(cand_root, files)

    for name in sorted(base):
        b, c = base[name], cand.get(name)
        if c is None:
            problems.append(f"verdict MISSING {name}")
            continue
        if b["conforms"] != c["conforms"]:
            problems.append(
                f"verdict DIFFERS {name}: baseline conforms={b['conforms']} "
                f"candidate conforms={c['conforms']}"
            )
            continue
        if b["violations"] != c["violations"]:
            delta = (b["violations"] - c["violations"]) | (
                c["violations"] - b["violations"]
            )
            unexplained = [item for item in delta if item[1] not in allowed_constraints]
            if not unexplained:
                accepted.append(
                    f"{name}: same verdict, "
                    f"{len(delta)} reported constraint(s) differ (all declared)"
                )
                continue
            problems.append(f"violations DIFFER {name}:")
            for item in sorted(b["violations"] - c["violations"]):
                if item in unexplained:
                    problems.append(f"    only baseline:  {item[1]} / {item[2]}")
            for item in sorted(c["violations"] - b["violations"]):
                if item in unexplained:
                    problems.append(f"    only candidate: {item[1]} / {item[2]}")
    return problems


# --------------------------------------------------------------------------
# layer 5: mutation probes
# --------------------------------------------------------------------------
XSD = "http://www.w3.org/2001/XMLSchema#"
_NUMERIC = {XSD + t for t in ("integer", "float", "decimal", "double", "int", "long")}


def _committed_shapes(repo_root: Path) -> Graph:
    """Every committed shapes file, not just the domain's own.

    A domain's instances are also validated against the shapes of the domains
    it builds on (an ositrace trace is an envited-x:SimulationAsset, its links
    are manifest:Links). Probing only the domain's own shapes cannot see a
    regression in any of those.
    """
    shapes = Graph()
    for path in sorted((repo_root / "artifacts").glob("*/*.shacl.ttl")):
        shapes.parse(path, format="turtle")
    return shapes


def _property_constraints(shapes: Graph) -> Dict[URIRef, dict]:
    """Constraints the committed shapes put on each predicate IRI."""
    from rdflib.collection import Collection

    out: Dict[URIRef, dict] = defaultdict(dict)
    for pshape, _, path in shapes.triples((None, SH.path, None)):
        if not isinstance(path, URIRef):
            continue
        entry = out[path]
        members = shapes.value(pshape, SH["in"])
        if members is not None:
            entry["in"] = list(Collection(shapes, members))
        for key in (
            "datatype",
            "nodeKind",
            "minCount",
            "maxCount",
            "minInclusive",
            "pattern",
        ):
            value = shapes.value(pshape, SH[key])
            if value is not None:
                entry.setdefault(key, value)
    return dict(out)


def _at_least_one_of_groups(shapes: Graph) -> List[List[URIRef]]:
    """Node-level ``sh:or`` whose branches each require one path.

    ``sh:or ( [sh:path a; sh:minCount 1] [sh:path b; sh:minCount 1] )`` means
    "a or b". Deleting paths one at a time never violates it, so it needs its
    own probe: delete every path of the group at once.
    """
    from rdflib.collection import Collection

    groups: List[List[URIRef]] = []
    for _, _, lst in shapes.triples((None, SH["or"], None)):
        paths: List[URIRef] = []
        for branch in Collection(shapes, lst):
            path = shapes.value(branch, SH.path)
            minimum = shapes.value(branch, SH.minCount)
            if isinstance(path, URIRef) and minimum is not None and int(minimum) >= 1:
                paths.append(path)
        if len(paths) >= 2:
            groups.append(sorted(paths))
    return groups


def _value_mutations(constraints: dict, obj) -> List[Tuple[str, object]]:
    """Replacement values that the committed constraints should reject."""
    out: List[Tuple[str, object]] = []
    if "in" in constraints:
        iri_valued = any(isinstance(v, URIRef) for v in constraints["in"])
        out.append(
            (
                "enum",
                URIRef("urn:x-probe:not-permitted")
                if iri_valued
                else Literal("__NOT_A_PERMITTED_VALUE__"),
            )
        )
    datatype = str(constraints.get("datatype", ""))
    if datatype in _NUMERIC:
        out.append(("datatype", Literal("not-a-number")))
    elif datatype == XSD + "dateTime":
        out.append(("datatype", Literal("not-a-timestamp")))
    elif datatype == XSD + "anyURI":
        out.append(("datatype", Literal(12345)))
    if str(constraints.get("nodeKind", "")) == str(SH.IRI) and isinstance(obj, URIRef):
        out.append(("nodeKind", Literal(str(obj))))
    if "pattern" in constraints and isinstance(obj, Literal):
        out.append(("pattern", Literal("no pattern match here")))
    if "minInclusive" in constraints and isinstance(obj, Literal):
        try:
            out.append(
                ("minInclusive", Literal(float(constraints["minInclusive"]) - 1))
            )
        except (TypeError, ValueError):
            pass
    return out


def _load_instance(root: Path, instance: Path) -> Graph:
    """Load an instance exactly as the validator does, contexts resolved locally."""
    from omb.utils.context_resolver import build_context_url_map
    from omb.utils.graph_loader import load_jsonld_files
    from omb.utils.registry_resolver import RegistryResolver

    url_map = build_context_url_map(RegistryResolver(root), root)
    graph, _ = load_jsonld_files([instance], root, context_url_map=url_map)
    return graph


def build_probes(
    instances: Sequence[Path],
    base_root: Path,
    repo_root: Path,
    outdir: Path,
    limit: int = 0,
) -> List[Tuple[Path, Path]]:
    """Derive adversarial instances from every committed shape, in RDF space.

    Each valid instance is loaded through the repository's own loader, mutated
    triple by triple, and written back as context-free expanded JSON-LD. Working
    on triples rather than JSON keys means no term has to be resolved, so
    constraints contributed by *other* domains are probed as well.
    """
    shapes = _committed_shapes(repo_root)
    constraints = _property_constraints(shapes)
    groups = _at_least_one_of_groups(shapes)

    outdir.mkdir(parents=True, exist_ok=True)
    made: List[Tuple[Path, Path]] = []
    current: List[Path] = []

    def emit(graph: Graph, stem: str, label: str) -> None:
        path = outdir / f"{stem}__{label}__{len(made)}.json"
        path.write_text(graph.serialize(format="json-ld"), encoding="utf-8")
        made.append((path, current[0]))

    for instance in instances:
        if "invalid" in instance.parts:
            continue
        original = _load_instance(base_root, instance)
        current[:] = [instance]
        stem = instance.stem
        triples = sorted(original, key=lambda tr: (str(tr[0]), str(tr[1]), str(tr[2])))
        for s, p, o in triples:
            entry = constraints.get(p)
            if not entry:
                continue
            local = str(p).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            for label, replacement in _value_mutations(entry, o):
                mutant = Graph()
                mutant += original
                mutant.remove((s, p, o))
                mutant.add((s, p, replacement))
                emit(mutant, stem, f"{local}-{label}")
            if entry.get("minCount") is not None and int(entry["minCount"]) >= 1:
                mutant = Graph()
                mutant += original
                mutant.remove((s, p, None))
                emit(mutant, stem, f"{local}-missing")
            if entry.get("maxCount") is not None and int(entry["maxCount"]) == 1:
                mutant = Graph()
                mutant += original
                extra = Literal(f"{o}-duplicate") if isinstance(o, Literal) else BNode()
                mutant.add((s, p, extra))
                emit(mutant, stem, f"{local}-maxCount")
        for group in groups:
            subjects = {s for path in group for s in original.subjects(path, None)}
            for s in sorted(subjects, key=str):
                mutant = Graph()
                mutant += original
                for path in group:
                    mutant.remove((s, path, None))
                names = "+".join(str(x).rsplit("/", 1)[-1] for x in group)
                emit(mutant, stem, f"none-of-{names}")

    if limit and len(made) > limit:
        # Deterministic stride, so a sampled run still spreads across every
        # instance and mutation kind rather than truncating to the first file.
        stride = len(made) / limit
        made = [made[int(i * stride)] for i in range(limit)]
    return made


def compare_probes(
    base_root: Path, cand_root: Path, probes: Sequence[Tuple[Path, Path]]
) -> Tuple[List[str], int, int, List[str]]:
    """Does each mutation introduce a violation, on each side?

    Comparing plain conformance verdicts is not enough: if a side already
    rejects the *unmutated* instance, every probe derived from it reads as
    "rejected" and discriminates nothing. A probe therefore counts as caught
    only when its violations are a strict addition to those of the instance it
    was derived from, judged separately on each side.
    """
    problems: List[str] = []
    references = sorted({ref for _, ref in probes}, key=str)
    files = [p for p, _ in probes]
    base_ref = run_validation(base_root, references)
    cand_ref = run_validation(cand_root, references)
    base = run_validation(base_root, files)
    cand = run_validation(cand_root, files)

    notes = [
        f"{ref.name}: baseline does not conform before mutation "
        f"({len(base_ref[ref.name]['violations'])} violation(s)) - probes are "
        "judged by added violations only"
        for ref in references
        if not base_ref[ref.name]["conforms"]
    ]

    discriminating = 0
    for path, ref in probes:
        b_new = base[path.name]["violations"] - base_ref[ref.name]["violations"]
        c_new = cand[path.name]["violations"] - cand_ref[ref.name]["violations"]
        if b_new:
            discriminating += 1
        if bool(b_new) != bool(c_new):
            problems.append(
                f"probe DIFFERS   {path.name}: baseline catches={bool(b_new)} "
                f"candidate catches={bool(c_new)}"
            )
    return problems, discriminating, len(probes), notes


# --------------------------------------------------------------------------
def load_exceptions(path: Path) -> dict:
    """Read the domain's declared, reviewed deviations.

    A deviation listed here is reported as accepted rather than failing the
    run, so every difference between the two artifact sets is either fixed or
    written down with a reason - never silently tolerated.
    """
    if not path.exists():
        return {}
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True)
    parser.add_argument(
        "--candidate", required=True, type=Path, help="directory of candidate artifacts"
    )
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument(
        "--with",
        dest="with_candidates",
        action="append",
        default=[],
        metavar="DOMAIN=DIR",
        help="also swap this candidate domain in on the candidate side "
        "(repeatable), for a candidate that depends on another candidate",
    )
    parser.add_argument("--layers", nargs="*", default=list(LAYERS), choices=LAYERS)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--max-probes",
        type=int,
        default=0,
        help="sample at most this many mutation probes (0 = all); "
        "a full ositrace run is 236 probes validated twice",
    )
    args = parser.parse_args(argv)

    repo_root: Path = args.repo_root.resolve()
    domain: str = args.domain
    baseline: Path = (args.baseline or repo_root / "artifacts" / domain).resolve()
    candidate: Path = args.candidate.resolve()
    with_candidates: Dict[str, Path] = {}
    for spec in args.with_candidates:
        name, _, path = spec.partition("=")
        if not name or not path:
            parser.error(f"--with expects DOMAIN=DIR, got {spec!r}")
        with_candidates[name] = Path(path).resolve()

    base_owl_file = baseline / f"{domain}.owl.ttl"
    cand_owl_file = candidate / f"{domain}.owl.ttl"
    for path in (base_owl_file, cand_owl_file):
        if not path.exists():
            print(f"[ERR] missing {path}", file=sys.stderr)
            return 2

    base_owl, cand_owl = Graph(), Graph()
    base_owl.parse(base_owl_file, format="turtle")
    cand_owl.parse(cand_owl_file, format="turtle")

    ontology = _ontology_node(base_owl)
    namespace = str(ontology) + "/" if ontology else ""

    data_dir = repo_root / "tests" / "data" / domain
    instances = sorted(data_dir.rglob("*.json"))

    exceptions = load_exceptions(
        repo_root / "linkml" / domain / "equivalence-exceptions.yaml"
    )
    allowed_terms = {e["term"] for e in exceptions.get("context", []) if "term" in e}
    allowed_constraints = {
        e["constraint"] for e in exceptions.get("shacl", []) if "constraint" in e
    }

    findings: Dict[str, List[str]] = {}
    advisory: List[str] = []
    accepted: List[str] = []
    if "header" in args.layers:
        findings["header"] = compare_header(base_owl, cand_owl, advisory)
    if "vocab" in args.layers:
        findings["vocab"] = compare_vocab(base_owl, cand_owl, namespace, advisory)
        cand_shacl = Graph()
        shacl_file = candidate / f"{domain}.shacl.ttl"
        if shacl_file.exists():
            cand_shacl.parse(shacl_file, format="turtle")
        for iri, count in sorted(unexpanded_iris(cand_owl, cand_shacl).items()):
            findings["vocab"].append(f"unexpanded IRI  <{iri}> ({count} use(s))")
    if "context" in args.layers:
        base_ctx = baseline / f"{domain}.context.jsonld"
        cand_ctx = candidate / f"{domain}.context.jsonld"
        if base_ctx.exists() and cand_ctx.exists():
            findings["context"] = compare_context(
                base_ctx, cand_ctx, instances, allowed_terms, accepted
            )
        else:
            findings["context"] = ["context file missing on one side"]
    probe_stats = None
    if "shacl" in args.layers or "probe" in args.layers:
        with tempfile.TemporaryDirectory(prefix="omb-equiv-") as tmp:
            workdir = Path(tmp)
            base_root = build_shadow_root(repo_root, domain, baseline, workdir / "b")
            cand_root = build_shadow_root(
                repo_root, domain, candidate, workdir / "c", extra=with_candidates
            )
            if "shacl" in args.layers:
                findings["shacl"] = compare_shacl(
                    base_root, cand_root, instances, allowed_constraints, accepted
                )
            if "probe" in args.layers:
                probes = build_probes(
                    instances, base_root, repo_root, workdir / "probes", args.max_probes
                )
                problems, discriminating, total, notes = compare_probes(
                    base_root, cand_root, probes
                )
                findings["probe"] = problems
                probe_stats = (discriminating, total)
                advisory.extend(notes)

    failed = False
    for layer in args.layers:
        problems = findings.get(layer, [])
        status = "OK" if not problems else f"{len(problems)} difference(s)"
        extra = ""
        if layer == "probe" and probe_stats:
            discriminating, total = probe_stats
            extra = f"  [{discriminating}/{total} probes caught by baseline]"
        print(f"\n=== {layer.upper():<8} {status}{extra}")
        for line in problems:
            print(f"  {line}")
        failed = failed or bool(problems)

    if accepted:
        print("\n=== ACCEPTED DEVIATIONS (declared in equivalence-exceptions.yaml)")
        for line in accepted:
            print(f"  {line}")
    if advisory:
        print("\n=== ADVISORY (additive, not a failure)")
        for line in advisory:
            print(f"  {line}")
    print("\n" + ("EQUIVALENT" if not failed else "NOT EQUIVALENT"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
