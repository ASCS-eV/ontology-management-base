#!/usr/bin/env python3
"""Prove that a LinkML-generated JSON Schema faithfully re-models a normative
reference JSON Schema, within a declared scope.

This tool is **ontology-independent**: it knows nothing about OpenLABEL. Point it
at any normative reference JSON Schema and any LinkML-generated JSON Schema (plus
a small per-migration spec) and it produces a scientific refinement proof. Reuse
it to validate every JSON-Schema -> LinkML migration in the repository.

The claim it tests (a falsifiable refinement relation)::

    Let A   = reference JSON Schema
        A|t = A projected onto the declared scope (reachability-closed subset)
        L   = LinkML-generated JSON Schema

    Soundness     : for all x. L accepts x  =>  A accepts x, or every reason A
                    rejects x is a declared relaxation (Lambda) at a location
                    that relaxation names. (Everything L calls valid, A also
                    calls valid, up to Lambda.) One counterexample refutes it.
    Bnd. complete : for all x. A|t accepts x  =>  L accepts x  OR  x in Delta
                    (Delta = the enumerated, justified stricter-set: added enums,
                    required fields, const pins, closed objects).

Three pillars, all programmatic:

    1. Scope projection   -- decidable. $ref reachability from declared entry
                             points partitions reference defs into in/out of scope.
    2. Structural gaps    -- decidable. Walk both schemas, emit one classified row
                             per (def, aspect): EQUIVALENT / REFINEMENT /
                             OUT_OF_SCOPE / LOOSER / UNMAPPED.
    3. Differential oracle -- empirical. Generate an instance corpus (mutation +
                             property-based via hypothesis-jsonschema), validate
                             against both schemas, bucket the verdict pairs.

Usage::

    python scripts/schema_refinement_prover.py --spec linkml/openlabel-tagging/proof_spec.yaml
    python scripts/schema_refinement_prover.py --spec <spec> --out REFINEMENT_PROOF.md
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from omb.core.logging import configure_cli_logging, get_logger

logger = get_logger(__name__)


# =============================================================================
# Data model
# =============================================================================

# Gap classifications.
EQUIVALENT = "EQUIVALENT"
REFINEMENT = "REFINEMENT"  # L stricter than A (intended, in Delta)
OUT_OF_SCOPE = "OUT_OF_SCOPE"  # A def deliberately not modelled
LOOSER = "LOOSER"  # L accepts more than A -- a soundness concern
UNMAPPED = "UNMAPPED"  # in-scope A def with no L counterpart -- a gap


@dataclass
class GapRow:
    ref_def: str
    linkml_def: str
    aspect: str
    classification: str
    detail: str
    justification: str = ""


@dataclass
class Buckets:
    """Verdict-pair tally for a differential corpus."""

    agree_accept: int = 0
    agree_reject: int = 0
    linkml_stricter: list[dict] = field(default_factory=list)  # A accept / L reject
    linkml_looser: list[dict] = field(
        default_factory=list
    )  # A reject / L accept, UNDISCLOSED (BUG)
    disclosed_looser: list[dict] = field(
        default_factory=list
    )  # A reject / L accept, declared/benign
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (
            self.agree_accept
            + self.agree_reject
            + len(self.linkml_stricter)
            + len(self.linkml_looser)
            + len(self.disclosed_looser)
        )

    def looseness_breakdown(self) -> dict[str, int]:
        """Instances per declared category."""
        counts: dict[str, int] = {}
        for s in self.disclosed_looser:
            for c in {d.split(" @ ", 1)[0] for d in s["declarations"]}:
                counts[c] = counts.get(c, 0) + 1
        return counts

    def declaration_hits(self) -> dict[str, int]:
        """Instances per declaration ("category @ where")."""
        counts: dict[str, int] = {}
        for s in self.disclosed_looser:
            for d in s["declarations"]:
                counts[d] = counts.get(d, 0) + 1
        return counts


@dataclass
class ProofReport:
    name: str
    in_scope: list[str]
    out_scope: list[str]
    gaps: list[GapRow]
    soundness: Buckets
    completeness: Buckets
    corpus_sizes: dict[str, int]
    unmapped: list[str]
    declared: list[str] = field(default_factory=list)
    spine: list[str] = field(default_factory=list)

    @property
    def observed_relaxations(self) -> set[str]:
        """Declarations ("category @ where") some instance actually needed."""
        seen = set(self.soundness.declaration_hits())
        seen |= set(self.completeness.declaration_hits())
        return seen

    @property
    def unobserved_relaxations(self) -> list[str]:
        """Declarations nothing needed. Each is checked per location: a stale
        one still widens what the gate accepts there, so it must be removed
        rather than kept around."""
        return sorted(set(self.declared) - self.observed_relaxations)

    @property
    def oracle_errors(self) -> list[str]:
        return self.soundness.errors + self.completeness.errors

    @property
    def structural_looser(self) -> list[GapRow]:
        """LOOSER gap rows. Each describes a whole definition rather than a
        location, so no location-bound relaxation can disclose one: every such
        row has to be fixed in the model."""
        return [g for g in self.gaps if g.classification == LOOSER]

    @property
    def vacuous(self) -> bool:
        """True when the differential oracle validated no instances at all.

        An empty corpus makes every "no counterexample found" statement true by
        default, so the soundness gate would pass without having tested
        anything. That is indistinguishable from a real proof in the report but
        carries none of the evidence, so it must never be reported as PROVEN.
        A seed glob that matches nothing is rejected before this point."""
        return self.soundness.total == 0

    @property
    def sound(self) -> bool:
        """No UNDISCLOSED way for L to accept what A rejects, and no in-scope
        definition left unmodelled. Disclosed, justified relaxations (declared
        in the spec's allow_looseness) do not break the relation.

        Requires a non-empty differential corpus: a gate that examined zero
        instances has not proven anything. An instance the oracle could not
        validate is likewise evidence missing, not evidence of agreement."""
        return (
            not self.vacuous
            and not self.oracle_errors
            and not self.soundness.linkml_looser
            and not self.completeness.linkml_looser
            and not self.structural_looser
            and not self.unmapped
        )

    @property
    def passes(self) -> bool:
        """The gate: a sound refinement whose every declared relaxation was
        needed somewhere."""
        return self.sound and not self.unobserved_relaxations

    def verdict(self) -> str:
        if self.vacuous:
            return "INCONCLUSIVE (empty differential corpus -- nothing was tested)"
        if not self.sound:
            return "REFUTED"
        if self.unobserved_relaxations:
            return (
                "PROVEN, BUT Λ IS STALE (declared relaxations no instance needed: "
                + ", ".join(self.unobserved_relaxations)
                + " -- remove them)"
            )
        return "PROVEN (sound refinement modulo declared relaxations)"


# =============================================================================
# Pillar 1 -- scope projection ($ref reachability)
# =============================================================================


def _defs_key(schema: dict) -> str:
    """Return whichever definitions container the schema uses."""
    if "definitions" in schema:
        return "definitions"
    return "$defs"


class _Refs:
    """``$ref`` resolution for one schema document, delegated to ``referencing``.

    Scope projection reasons about *definitions*, so a reference is only
    meaningful here if it lands on a top-level entry of the schema's definitions
    container. Anything else (an external document, a pointer into the middle of
    a definition) is rejected instead of being guessed from its last segment.
    """

    _BASE = "urn:schema-refinement-prover:document"

    def __init__(self, schema: dict) -> None:
        uri = schema.get("$id") or self._BASE
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        self._resolver = Registry().with_resource(uri, resource).resolver(base_uri=uri)
        defs = schema.get(_defs_key(schema), {})
        self._names = {id(v): k for k, v in defs.items()}

    def lookup(self, ref: str) -> Any:
        return self._resolver.lookup(ref).contents

    def def_name(self, ref: str) -> str:
        try:
            return self._names[id(self.lookup(ref))]
        except KeyError:
            raise ValueError(
                f"$ref {ref!r} does not point at a top-level definition"
            ) from None


def _collect_refs(node: Any, acc: set[str], refs: _Refs) -> None:
    """Add the definition name of every ``$ref`` below *node* to *acc*."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str):
                acc.add(refs.def_name(v))
            else:
                _collect_refs(v, acc, refs)
    elif isinstance(node, list):
        for item in node:
            _collect_refs(item, acc, refs)


def _navigate(schema: dict, dotted: str) -> dict | None:
    """Resolve a dotted property path (e.g. 'openlabel.metadata') to a subschema,
    following 'properties' at each step and resolving intermediate $refs."""
    node: Any = schema
    for part in dotted.split("."):
        node = _resolve_ref(schema, node)
        if not isinstance(node, dict):
            return None
        props = node.get("properties", {})
        if part not in props:
            return None
        node = props[part]
    return node


def _resolve_ref(schema: dict, node: Any) -> Any:
    """Follow ``$ref`` chains from *node* until a non-reference subschema."""
    refs = _Refs(schema)
    seen: set[str] = set()
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if ref in seen:
            raise ValueError(f"$ref cycle without content at {ref!r}")
        seen.add(ref)
        node = refs.lookup(ref)
    return node


def project_scope(
    schema: dict, keep_paths: list[str] | None
) -> tuple[set[str], set[str]]:
    """Partition reference definitions into (in_scope, out_of_scope).

    in_scope = transitive $ref closure of every kept path. If keep_paths is None
    the whole schema is in scope (full-equivalence migrations)."""
    dk = _defs_key(schema)
    all_defs = set(schema.get(dk, {}))
    if not keep_paths:
        return all_defs, set()

    refs = _Refs(schema)
    roots: list[Any] = []
    for path in keep_paths:
        node = _navigate(schema, path)
        if node is None:
            # A scope path that resolves to nothing would silently shrink the
            # scope -- and with it everything the proof claims to cover.
            raise ValueError(f"scope path {path!r} does not resolve in the schema")
        roots.append(node)
    reach = _ref_closure(schema, roots, refs)

    in_scope = reach & all_defs
    return in_scope, all_defs - in_scope


def spine_defs(schema: dict, keep_paths: list[str] | None) -> set[str]:
    """Definitions the kept paths run through on their way to the kept nodes
    (the containers above the scope, such as OpenLABEL's ``openlabel``). They
    are neither in scope (only their kept members are) nor out of it."""
    refs = _Refs(schema)
    found: set[str] = set()
    for path in keep_paths or []:
        node: Any = schema
        for part in path.split("."):
            while isinstance(node, dict) and isinstance(node.get("$ref"), str):
                found.add(refs.def_name(node["$ref"]))
                node = refs.lookup(node["$ref"])
            node = (
                node.get("properties", {}).get(part) if isinstance(node, dict) else None
            )
    return found


def build_projected_schema(schema: dict, keep_paths: list[str] | None) -> dict:
    """Return A|t: a self-contained copy of the reference schema pruned to scope,
    suitable for property-based generation of in-scope-valid instances."""
    if not keep_paths:
        return copy.deepcopy(schema)

    proj = copy.deepcopy(schema)
    dk = _defs_key(proj)

    # Build a trie of kept property paths.
    trie: dict = {}
    for path in keep_paths:
        cur = trie
        for part in path.split("."):
            cur = cur.setdefault(part, {})

    refs = _Refs(proj)

    def prune(node: Any, sub: dict) -> None:
        if not isinstance(node, dict) or not sub:
            return  # leaf of the keep-trie: retain node entirely
        while isinstance(node.get("$ref"), str):
            # Prune a copy of the referenced definition in place of the
            # reference, never the shared definition itself: another path may
            # still need all of it. Nested references keep resolving against
            # the root, so the copy stays valid where it now sits; a chain of
            # references is followed to its end.
            target = copy.deepcopy(refs.lookup(node.pop("$ref")))
            node.update({k: v for k, v in target.items() if k not in node})
        props = node.get("properties")
        if isinstance(props, dict):
            for name in list(props):
                if name not in sub:
                    del props[name]
                else:
                    prune(props[name], sub[name])
        req = node.get("required")
        if isinstance(req, list):
            node["required"] = [r for r in req if not props or r in props]

    prune(proj, trie)

    # Keep exactly the defs still reachable from the pruned root. The spine
    # definitions were inlined above, so only the scope's own remain.
    reach = _reachable_from_root(proj)
    proj[dk] = {k: v for k, v in proj.get(dk, {}).items() if k in reach}
    return proj


def _ref_closure(schema: dict, roots: list[Any], refs: _Refs) -> set[str]:
    """Names of every definition reachable by ``$ref`` from *roots*."""
    defs = schema.get(_defs_key(schema), {})
    reach: set[str] = set()
    for node in roots:
        _collect_refs(node, reach, refs)
    frontier = set(reach)
    while frontier:
        nxt: set[str] = set()
        for d in frontier:
            _collect_refs(defs.get(d, {}), nxt, refs)
        nxt -= reach
        reach |= nxt
        frontier = nxt
    return reach


def _reachable_from_root(schema: dict) -> set[str]:
    """All definition names reachable by $ref from the schema root."""
    dk = _defs_key(schema)
    root = {k: v for k, v in schema.items() if k != dk}
    return _ref_closure(schema, [root], _Refs(schema))


def strip_properties(schema: dict, names: list[str]) -> dict:
    """Return a copy in which the named (optional) properties are forbidden.

    Used to break recursive cycles for property-based generation. Each property
    becomes the ``false`` schema rather than disappearing: deleting it would let
    an open object generate it as an arbitrary additional member, which the
    full schema rejects. Forbidden, it is simply never generated, so every
    generated instance stays valid against the full schema."""
    if not names:
        return schema
    s = copy.deepcopy(schema)
    drop = set(names)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                for nm in list(props):
                    if nm in drop:
                        props[nm] = False
                req = node.get("required")
                if isinstance(req, list):
                    node["required"] = [r for r in req if r not in drop]
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(s)
    return s


# =============================================================================
# Pillar 2 -- structural correspondence (the gap table)
# =============================================================================


def _prop_names(schema: dict, defn: dict) -> set[str]:
    defn = _resolve_ref(schema, defn)
    return set(defn.get("properties", {})) if isinstance(defn, dict) else set()


def match_definitions(
    ref: dict,
    linkml: dict,
    in_scope: set[str],
    explicit_map: dict[str, str],
) -> dict[str, str | None]:
    """Map each in-scope reference def to a LinkML def -- explicit first, then a
    Jaccard-of-property-names heuristic. Returns ref_def -> linkml_def | None."""
    ldk = _defs_key(linkml)
    rdk = _defs_key(ref)
    linkml_defs = linkml.get(ldk, {})
    mapping: dict[str, str | None] = {}

    for rd in sorted(in_scope):
        if rd in explicit_map:
            mapping[rd] = explicit_map[rd]
            continue
        rprops = _prop_names(ref, ref.get(rdk, {}).get(rd, {}))
        best, best_score = None, 0.0
        for ld, ldef in linkml_defs.items():
            lprops = _prop_names(linkml, ldef)
            union = rprops | lprops
            jac = len(rprops & lprops) / len(union) if union else 0.0
            # tie-break toward name similarity (case-insensitive containment)
            name_bonus = 0.15 if rd.lower().replace("_", "") in ld.lower() else 0.0
            score = jac + name_bonus
            if score > best_score:
                best, best_score = ld, score
        mapping[rd] = best if best_score >= 0.3 else None
    return mapping


def _json_types(schema: dict, prop: Any) -> set[str]:
    """Set of JSON 'type' tokens a property accepts (flattening list-types and
    anyOf/oneOf null-unions)."""
    prop = _resolve_ref(schema, prop)
    if not isinstance(prop, dict):
        return set()
    types: set[str] = set()
    t = prop.get("type")
    if isinstance(t, str):
        types.add(t)
    elif isinstance(t, list):
        types |= set(t)
    for key in ("anyOf", "oneOf"):
        for sub in prop.get(key, []):
            types |= _json_types(schema, sub)
    return types


# Looseness categories the oracle/structural checker can recognise. A category
# is only treated as benign when the spec's allow_looseness declares it, and only
# at the locations the declaration names.
KEY_PATTERN = "key_pattern"  # A constrains dict keys; L accepts any key
NULL_OPTIONAL = "null_optional"  # L permits explicit JSON null where A forbids it
# L permits the object form of a LinkML inlined simple-dict value (an object with
# the value slot) where A allows only the bare scalar. This is a LinkML
# expressivity limit: an inlined simple-dict cannot be restricted to scalar-only
# values, so the object form is always accepted.
SIMPLE_DICT_OBJECT_FORM = "simple_dict_object_form"
# L accepts content it deliberately does not validate: the location is handed to
# a definition whose $ref carries the spec's passthrough marker. Whatever A says
# about that content, L has declared it unchecked, so A's verdict there is not a
# soundness counterexample -- the profile never claimed to check it.
UNCHECKED_SECTION = "unchecked_section"

_PATH_CATEGORIES = {KEY_PATTERN, NULL_OPTIONAL, SIMPLE_DICT_OBJECT_FORM}
_ANNOTATIONS = {"title", "description", "$comment", "examples", "default"}
_COMBINATORS = {"$ref", "anyOf", "oneOf", "allOf"}


@dataclass(frozen=True)
class Relaxation:
    """A declared looseness category and the locations it is allowed at.

    ``paths`` are dotted instance locations with one ``fnmatch`` pattern per
    segment (``openlabel.tags.*.resource_uid.*``). ``marker`` is used by
    ``unchecked_section`` instead: a ``$ref`` prefix that identifies the
    passthrough definitions in L."""

    category: str
    paths: tuple[str, ...] = ()
    marker: str | None = None

    @property
    def declarations(self) -> list[str]:
        """One "category @ where" entry per declared location (or marker)."""
        return [f"{self.category} @ {w}" for w in (self.paths or (self.marker,))]

    def match(self, location: tuple) -> str | None:
        """The declared path pattern covering *location*, if any."""
        return next((p for p in self.paths if _path_matches(p, location)), None)


def _path_matches(pattern: str, location: tuple) -> bool:
    parts = pattern.split(".")
    return len(parts) == len(location) and all(
        fnmatchcase(str(seg), pat) for seg, pat in zip(location, parts)
    )


def parse_relaxations(cfg: Any) -> dict[str, Relaxation]:
    """Read a spec's ``allow_looseness`` mapping.

    Nothing is allowed unless declared: an absent mapping means a strict proof.
    Every declaration must say *where* it applies, so a relaxation granted for
    one field cannot absorb the same kind of error anywhere else."""
    if not cfg:
        return {}
    if not isinstance(cfg, dict):
        raise ValueError(
            "allow_looseness must map each category to where it applies "
            "(paths: [...], or marker: ... for unchecked_section)"
        )
    out: dict[str, Relaxation] = {}
    for category, decl in cfg.items():
        decl = decl or {}
        if category == UNCHECKED_SECTION:
            marker = decl.get("marker")
            if not marker:
                raise ValueError("unchecked_section needs a $ref 'marker'")
            out[category] = Relaxation(category, marker=marker)
        elif category in _PATH_CATEGORIES:
            paths = tuple(decl.get("paths") or ())
            if not paths:
                raise ValueError(f"{category} needs at least one 'paths' entry")
            out[category] = Relaxation(category, paths=paths)
        else:
            raise ValueError(f"unknown looseness category {category!r}")
    return out


def _unchecked_depth(
    schema: dict, location: tuple, marker: str, refs: _Refs
) -> int | None:
    """Length of the shortest prefix of *location* at which *schema* hands the
    instance to a definition whose ``$ref`` starts with *marker*, else None.

    Errs towards None ("checked"): a location counts as unchecked only when
    nothing else constrains it, so a wrong answer can make the gate fail, never
    pass."""

    def walk(node: Any, depth: int) -> int | None:
        if not isinstance(node, dict):
            return None
        # Any keyword besides the reference or combinator that leads to the
        # marker constrains this same instance (sibling keywords apply next to
        # $ref from draft 2019-09 on), so the location is at least partly
        # checked and is not reported as unchecked here.
        constrained = bool(set(node) - _COMBINATORS - _ANNOTATIONS)
        ref = node.get("$ref")
        if isinstance(ref, str):
            found = depth if ref.startswith(marker) else walk(refs.lookup(ref), depth)
            return None if constrained else found
        # anyOf/oneOf: L accepts what any branch accepts, so one unchecked
        # branch leaves the location unchecked. allOf: every branch must accept,
        # so the location is unchecked only if every branch is.
        if any(key in node for key in ("anyOf", "oneOf", "allOf")):
            if constrained:
                return None
            for key in ("anyOf", "oneOf"):
                for branch in node.get(key, []):
                    found = walk(branch, depth)
                    if found is not None:
                        return found
            branches = node.get("allOf", [])
            found = [walk(branch, depth) for branch in branches]
            if branches and all(f is not None for f in found):
                return max(found)
            return None
        if depth == len(location):
            return None
        seg = location[depth]
        if isinstance(seg, int):
            subs = [node["items"]] if "items" in node else []
        else:
            # JSON Schema applies the named property and every matching
            # pattern; additionalProperties only when neither applies.
            subs = (
                [node["properties"][seg]] if seg in node.get("properties", {}) else []
            )
            subs += [
                v
                for pattern, v in node.get("patternProperties", {}).items()
                if re.search(pattern, seg)
            ]
            if not subs and "additionalProperties" in node:
                subs = [node["additionalProperties"]]
        found = [walk(sub, depth + 1) for sub in subs]
        # Every applicable subschema has to leave the content unchecked.
        return max(found) if found and all(f is not None for f in found) else None

    return walk(schema, 0)


def _expects_scalar(validator_value: Any) -> bool:
    """True if a JSON Schema ``type`` keyword value names a scalar type."""
    scalars = {"string", "number", "integer", "boolean"}
    if isinstance(validator_value, str):
        return validator_value in scalars
    if isinstance(validator_value, list):
        return any(t in scalars for t in validator_value)
    return False


def _classify(
    error: Any, allowed: dict[str, Relaxation], linkml: dict, refs: _Refs
) -> str | None:
    """The declaration ("category @ where") covering one reference-schema
    error, or None if no declaration covers it at its location."""
    location = tuple(error.absolute_path)
    unchecked = allowed.get(UNCHECKED_SECTION)
    if unchecked is not None:
        depth = _unchecked_depth(linkml, location, unchecked.marker, refs)
        # Below the passthrough anchor everything is unchecked content. At the
        # anchor itself only the node's own type is still L's business: the
        # passthrough definitions are typed, so a wrong type there is not
        # something L declared it would skip.
        if depth is not None and (len(location) > depth or error.validator != "type"):
            return unchecked.declarations[0]
    if error.validator in ("additionalProperties", "patternProperties"):
        category = KEY_PATTERN
    elif error.validator == "type" and error.instance is None:
        category = NULL_OPTIONAL
    elif (
        error.validator == "type"
        and isinstance(error.instance, dict)
        and _expects_scalar(error.validator_value)
    ):
        category = SIMPLE_DICT_OBJECT_FORM
    else:
        return None
    rule = allowed.get(category)
    where = rule.match(location) if rule is not None else None
    return f"{category} @ {where}" if where is not None else None


def categorize_looseness(
    errors: list, allowed: dict[str, Relaxation], linkml: dict, refs: _Refs
) -> set[str] | None:
    """Classify why A rejected an instance L accepted.

    Returns the declarations ("category @ where") that cover the errors iff
    EVERY reference-schema error is covered by a declaration for its location
    (benign, disclosed looseness). Returns None if any error is not -- i.e. a
    real, undisclosed soundness violation."""
    found: set[str] = set()
    for e in errors:
        declaration = _classify(e, allowed, linkml, refs)
        if declaration is None:
            return None
        found.add(declaration)
    return found


def _enum_of(schema: dict, prop: dict) -> set[str] | None:
    prop = _resolve_ref(schema, prop)
    if not isinstance(prop, dict):
        return None
    if "enum" in prop:
        return set(prop["enum"])
    if "const" in prop:
        return {prop["const"]}
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in prop.get(key, []):
            e = _enum_of(schema, sub)
            if e:
                return e
    return None


def _is_object_schema(node: Any) -> bool:
    return isinstance(node, dict) and (
        node.get("type") == "object" or "properties" in node
    )


def _object_view(schema: dict, node: Any) -> Any:
    """The object-shaped subschema a definition contributes to comparison.

    Follows ``$ref``; enters the value schema of a pattern-keyed map (A's
    ``ontologies``, ``resources`` and ``resource_uid`` are maps of entries, and
    are mapped to L's entry classes); and takes the object branch of a
    ``oneOf``/``anyOf`` (A's ``tag_data`` and ontology entries are either a
    string or an object)."""
    node = _resolve_ref(schema, node)
    if not isinstance(node, dict):
        return node
    patterns = node.get("patternProperties")
    if isinstance(patterns, dict) and len(patterns) == 1 and not node.get("properties"):
        node = _resolve_ref(schema, next(iter(patterns.values())))
    if isinstance(node, dict) and not _is_object_schema(node):
        for key in ("oneOf", "anyOf"):
            for branch in node.get(key, []):
                branch = _resolve_ref(schema, branch)
                if _is_object_schema(branch):
                    return branch
    return node


def structural_gaps(
    ref: dict,
    linkml: dict,
    in_scope: set[str],
    out_scope: set[str],
    mapping: dict[str, str | None],
    justifier,
) -> tuple[list[GapRow], list[str]]:
    """Emit classified gap rows for every in-scope def + every out-of-scope def.
    Returns (rows, unmapped_in_scope_defs).

    A LOOSER row describes a whole definition, not a location, so no declared
    relaxation -- each is bound to locations -- can disclose it: every LOOSER
    row is undisclosed and has to be fixed in the model."""
    rows: list[GapRow] = []
    unmapped: list[str] = []
    rdk, ldk = _defs_key(ref), _defs_key(linkml)

    for rd in sorted(out_scope):
        rows.append(
            GapRow(
                rd,
                "-",
                "definition",
                OUT_OF_SCOPE,
                "outside the declared scope",
                justifier(rd, "out_of_scope", OUT_OF_SCOPE),
            )
        )

    for rd in sorted(in_scope):
        ld = mapping.get(rd)
        if ld is None:
            unmapped.append(rd)
            rows.append(
                GapRow(
                    rd,
                    "?",
                    "definition",
                    UNMAPPED,
                    "in scope but no LinkML counterpart",
                    justifier(rd, "unmapped", UNMAPPED),
                )
            )
            continue

        rdef = _object_view(ref, ref.get(rdk, {}).get(rd, {}))
        ldef = _object_view(linkml, linkml.get(ldk, {}).get(ld, {}))
        if not _is_object_schema(rdef) or not _is_object_schema(ldef):
            # Nothing object-shaped to compare, e.g. A's value is a plain string
            # where L models an inlined simple dict. The oracle covers that
            # case, under its location-bound declaration.
            continue

        # required-field refinement
        rreq, lreq = set(rdef.get("required", [])), set(ldef.get("required", []))
        added = lreq - rreq
        dropped = rreq - lreq
        if added:
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "required",
                    REFINEMENT,
                    f"L additionally requires {sorted(added)}",
                    justifier(rd, "required", REFINEMENT),
                )
            )
        if dropped:
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "required",
                    LOOSER,
                    f"L drops required {sorted(dropped)}",
                    justifier(rd, "required_dropped", LOOSER),
                )
            )

        # closed-object refinement
        r_add = rdef.get("additionalProperties", True)
        l_add = ldef.get("additionalProperties", True)
        if r_add is not False and l_add is False:
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "additionalProperties",
                    REFINEMENT,
                    "L closes the object (A is open)",
                    justifier(rd, "closed", REFINEMENT),
                )
            )
        # per-property enum + null-permissiveness refinements
        rprops = rdef.get("properties", {})
        lprops = ldef.get("properties", {})
        null_props: list[str] = []
        for pname in sorted(set(rprops) & set(lprops)):
            r_types = _json_types(ref, rprops[pname])
            l_types = _json_types(linkml, lprops[pname])
            if "null" in l_types and "null" not in r_types and r_types:
                null_props.append(pname)
            r_enum = _enum_of(ref, rprops[pname])
            l_enum = _enum_of(linkml, lprops[pname])
            if l_enum and not r_enum:
                rows.append(
                    GapRow(
                        rd,
                        ld,
                        f"{pname} (enum)",
                        REFINEMENT,
                        f"A: unconstrained -> L: enum of {len(l_enum)}",
                        justifier(rd, f"{pname}.enum", REFINEMENT),
                    )
                )
            elif r_enum and l_enum:
                if l_enum - r_enum:
                    rows.append(
                        GapRow(
                            rd,
                            ld,
                            f"{pname} (enum)",
                            LOOSER,
                            f"L enum adds values absent from A: "
                            f"{sorted(l_enum - r_enum)}",
                            justifier(rd, f"{pname}.enum_extra", LOOSER),
                        )
                    )
                elif r_enum - l_enum:
                    rows.append(
                        GapRow(
                            rd,
                            ld,
                            f"{pname} (enum)",
                            REFINEMENT,
                            f"L narrows A enum (drops {sorted(r_enum - l_enum)})",
                            justifier(rd, f"{pname}.enum_narrow", REFINEMENT),
                        )
                    )
        if null_props:
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "null-permissive",
                    LOOSER,
                    f"{len(null_props)} optional field(s) accept explicit "
                    f"null in L but not A: {null_props}",
                    justifier(rd, "null_optional", LOOSER),
                )
            )
        # Members only L names: L constrains what an open A leaves free, or
        # admits what a closed A forbids.
        l_only = sorted(set(lprops) - set(rprops))
        if l_only and r_add is not False:
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "members only L constrains",
                    REFINEMENT,
                    f"A leaves {l_only} open; L constrains them",
                    justifier(rd, "members", REFINEMENT),
                )
            )
        elif l_only:
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "members A forbids",
                    LOOSER,
                    f"A is closed, but L accepts {l_only}",
                    justifier(rd, "members", LOOSER),
                )
            )
    return rows, unmapped


# =============================================================================
# Pillar 3 -- differential oracle
# =============================================================================


def make_validator(schema: dict):
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def validate(validator, instance: Any) -> tuple[bool, list]:
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    return (not errors), errors


def mutation_corpus(seeds: list[Any]) -> list[tuple[str, Any]]:
    """Deterministically derive malformed/edge instances from valid seeds.

    At every location of every seed -- object members and array items alike --
    drop it, swap it for each value in ``_SWAPS`` (containers included, so a
    section entry also becomes null, a scalar or an empty container), and inject
    an unexpected member into each object. Every object member is also re-keyed: the same,
    well-formed value under a key no schema allows, which is the only way a key
    constraint (``propertyNames``, ``patternProperties``) is tested on its own.
    Locations are carried as tuples of keys and indices, never as parsed
    strings, so a dict key such as ``"0"`` (every OpenLABEL UID) stays a key and
    the mutations reach the tag data."""
    out: list[tuple[str, Any]] = []
    for si, seed in enumerate(seeds):
        name = f"seed{si}"
        out.append((name, copy.deepcopy(seed)))
        for location, value in _locations(seed):
            label = _label(location)
            if location:
                out.append((f"{name}:drop:{label}", _mutated(seed, location, _drop)))
            if location and isinstance(location[-1], str):
                out.append((f"{name}:rekey:{label}", _mutated(seed, location, _rekey)))
            if location:
                for swap in _SWAPS:
                    if type(swap) is type(value) and swap == value:
                        continue  # identical to the seed (True == 1, so compare types)
                    out.append(
                        (
                            f"{name}:swap:{label}={swap!r}",
                            _mutated(seed, location, _replace_with(swap)),
                        )
                    )
            if isinstance(value, dict):
                out.append(
                    (f"{name}:inject:{label}", _mutated(seed, location, _inject))
                )
    return out


_SWAPS = (None, "___JUNK___", 12345, 3.14, True, [], {})


def _locations(node: Any, location: tuple = ()) -> Iterable[tuple[tuple, Any]]:
    """Every (location, value) pair of a JSON document, parents first."""
    yield location, node
    if isinstance(node, dict):
        for key, child in node.items():
            yield from _locations(child, location + (key,))
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from _locations(child, location + (index,))


def _label(location: tuple) -> str:
    """Readable case label for a location (a name in the report, not a format)."""
    return "$" + "".join(f"[{seg!r}]" for seg in location)


def _mutated(seed: Any, location: tuple, mutate) -> Any:
    """A deep copy of *seed* with *mutate* applied at *location*."""
    doc = copy.deepcopy(seed)
    if not location:
        mutate(None, None, doc)
        return doc
    parent = doc
    for seg in location[:-1]:
        parent = parent[seg]
    mutate(parent, location[-1], parent[location[-1]])
    return doc


def _drop(parent: Any, key: Any, _value: Any) -> None:
    del parent[key]


_BAD_KEY = "___unexpected key___"


def _rekey(parent: Any, key: Any, value: Any) -> None:
    del parent[key]
    parent[_BAD_KEY] = value


def _replace_with(swap: Any):
    def mutate(parent: Any, key: Any, _value: Any) -> None:
        parent[key] = copy.deepcopy(swap)

    return mutate


def _inject(_parent: Any, _key: Any, value: Any) -> None:
    value["___unexpected___"] = "x"


# Property-based generation runs in a worker process. Hypothesis mixes literal
# constants from every "local" module loaded in its process (not stdlib, not
# site-packages, not tests) into what it generates, so with derandomize=True the
# corpus still depends on what the calling process happened to import: an
# editable omb install, a test module collected earlier. The worker imports
# nothing but the standard library, hypothesis and hypothesis-jsonschema, so the
# same schema yields the same corpus from the CLI, from pytest and in CI.
_HYPOTHESIS_WORKER = """
import json, sys
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema

request = json.load(sys.stdin)
out = []

@settings(
    max_examples=request["n"],
    deadline=None,
    database=None,
    derandomize=True,
    suppress_health_check=list(HealthCheck),
)
@given(from_schema(request["schema"]))
def collect(example):
    out.append(example)

collect()
json.dump(out, sys.stdout)
"""


_WORKER_TIMEOUT_SECONDS = 900


def hypothesis_corpus(schema: dict, n: int) -> list[Any]:
    """Property-based instance generation from a (projected) schema.

    Runs in an isolated worker (see ``_HYPOTHESIS_WORKER``), and fails instead
    of returning fewer instances than requested: a corpus that quietly shrank
    would weaken the gate without changing its verdict."""
    if n <= 0:
        return []
    result = subprocess.run(
        [sys.executable, "-I", "-c", _HYPOTHESIS_WORKER],
        input=json.dumps({"schema": schema, "n": n}),
        capture_output=True,
        text=True,
        timeout=_WORKER_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"property-based generation failed:\n{result.stderr}")
    out = json.loads(result.stdout)
    if len(out) < n:
        raise RuntimeError(
            f"hypothesis generated {len(out)} of the {n} instances requested"
        )
    return out


def differential(
    corpus: Iterable[tuple[str, Any]],
    ref_validator,
    linkml_validator,
    allowed: dict[str, Relaxation],
    linkml: dict,
) -> Buckets:
    b = Buckets()
    refs = _Refs(linkml)
    for name, inst in corpus:
        try:
            a_ok, a_err = validate(ref_validator, inst)
            l_ok, _ = validate(linkml_validator, inst)
        except Exception as exc:  # recorded; ProofReport.sound treats it as a failure
            b.errors.append(f"{name}: {exc}")
            continue
        if a_ok and l_ok:
            b.agree_accept += 1
        elif not a_ok and not l_ok:
            b.agree_reject += 1
        elif a_ok and not l_ok:
            b.linkml_stricter.append({"case": name})
        else:  # not a_ok and l_ok  -> L accepts what A rejects
            found = categorize_looseness(a_err, allowed, linkml, refs)
            if found is None:
                b.linkml_looser.append(
                    {"case": name, "why": "; ".join(e.message for e in a_err[:2])}
                )
            else:
                b.disclosed_looser.append({"case": name, "declarations": sorted(found)})
    return b


# =============================================================================
# Orchestration
# =============================================================================


def _justification(
    configured: dict[str, str], ref_def: str, aspect_key: str, classification: str
) -> str:
    """The spec's justification for a gap row, else a generic one.

    A configured key matches when its dotted segments occur as a contiguous run
    in ``{ref_def}.{aspect_key}`` (``type.enum`` matches ``tag.type.enum``), or
    when it names the classification. Whole segments only: ``tag.required``
    must not justify ``tag.required_dropped``, which is the opposite finding."""
    key = f"{ref_def}.{aspect_key}".split(".")
    for pattern, text in configured.items():
        parts = pattern.split(".")
        if pattern == classification or any(
            key[i : i + len(parts)] == parts for i in range(len(key) - len(parts) + 1)
        ):
            return text
    return {
        OUT_OF_SCOPE: "Outside declared scope; unreachable from kept entry points.",
        REFINEMENT: "Intended strengthening (Delta): L validates what A leaves open.",
        LOOSER: "L is looser than A for the whole definition: fix the model.",
        UNMAPPED: "GAP: in-scope definition without a LinkML counterpart.",
    }.get(classification, "")


def prove(spec: dict, root: Path) -> ProofReport:
    name = spec.get("name", "migration")
    ref = json.loads((root / spec["reference_schema"]).read_text(encoding="utf-8"))
    linkml = json.loads((root / spec["linkml_schema"]).read_text(encoding="utf-8"))

    keep = spec.get("scope_keep")
    in_scope, out_scope = project_scope(ref, keep)
    spine = spine_defs(ref, keep)
    out_scope -= spine
    logger.info(
        "%s: %d in-scope defs, %d out-of-scope", name, len(in_scope), len(out_scope)
    )

    configured: dict[str, str] = spec.get("justifications", {})

    def justifier(ref_def: str, aspect_key: str, classification: str) -> str:
        return _justification(configured, ref_def, aspect_key, classification)

    allowed = parse_relaxations(spec.get("allow_looseness"))

    mapping = match_definitions(ref, linkml, in_scope, spec.get("def_map", {}))
    gaps, unmapped = structural_gaps(
        ref, linkml, in_scope, out_scope, mapping, justifier
    )

    ref_v = make_validator(ref)
    linkml_v = make_validator(linkml)

    # corpus
    seeds: list[Any] = []
    for g in spec.get("seeds", []):
        matched = sorted(root.glob(g))
        if not matched:
            # A mistyped glob would silently drop the whole mutation corpus.
            raise ValueError(f"seed glob {g!r} matches no file under {root}")
        for p in matched:
            seeds.append(json.loads(p.read_text(encoding="utf-8")))

    n_sound = int(spec.get("hypothesis", {}).get("soundness", 0))
    n_compl = int(spec.get("hypothesis", {}).get("completeness", 0))
    # Optional properties to drop for property-based GENERATION only, to break
    # recursive $ref cycles that hypothesis-jsonschema cannot expand. Pruned
    # subtrees are optional, so generated instances stay valid against the full
    # schema; the mutation corpus + seeds still exercise those subtrees.
    gen_prune = spec.get("generation_prune", [])

    # Soundness corpus: instances drawn from L's own grammar (+ seeds) -> must be A-valid.
    mutations = mutation_corpus(seeds)
    hyp_l = hypothesis_corpus(strip_properties(linkml, gen_prune), n_sound)
    sound_corpus = mutations + [(f"hypL{i}", inst) for i, inst in enumerate(hyp_l)]

    # Completeness corpus: A|t-valid instances -> measure how much stricter L is.
    projected = build_projected_schema(ref, keep)
    hyp_a = hypothesis_corpus(strip_properties(projected, gen_prune), n_compl)
    compl_corpus = [(f"hypA{i}", inst) for i, inst in enumerate(hyp_a)]
    compl_corpus += [(f"seed{si}", seed) for si, seed in enumerate(seeds)]

    soundness = differential(sound_corpus, ref_v, linkml_v, allowed, linkml)
    completeness = differential(compl_corpus, ref_v, linkml_v, allowed, linkml)

    return ProofReport(
        name=name,
        in_scope=sorted(in_scope),
        out_scope=sorted(out_scope),
        spine=sorted(spine),
        gaps=gaps,
        soundness=soundness,
        completeness=completeness,
        corpus_sizes={
            "seeds": len(seeds),
            "mutations": len(mutations) - len(seeds),
            "hypothesis_soundness": len(hyp_l),
            "hypothesis_completeness": len(hyp_a),
        },
        unmapped=unmapped,
        declared=sorted(d for rule in allowed.values() for d in rule.declarations),
    )


# =============================================================================
# Reporting
# =============================================================================


def report_markdown(
    r: ProofReport,
    allowed: dict[str, Relaxation],
    justifications: dict[str, str] | None = None,
) -> str:
    L: list[str] = []
    L.append(f"# Refinement Proof — `{r.name}`\n")
    L.append(
        "Auto-generated by `scripts/schema_refinement_prover.py`. Asserts that the "
        "LinkML-generated JSON Schema (L) is a **sound refinement** of the normative "
        "reference JSON Schema (A) within the declared scope. Regenerate after any "
        "schema or submodule change.\n"
    )
    L.append(f"**Verdict: {r.verdict()}**\n")

    L.append("## 1. Scope projection ($ref reachability)\n")
    L.append(
        f"- **In scope ({len(r.in_scope)} defs):** {', '.join(f'`{d}`' for d in r.in_scope)}"
    )
    if r.spine:
        L.append(
            f"- **Spine ({len(r.spine)} defs, containers above the scope, not "
            f"compared):** {', '.join(f'`{d}`' for d in r.spine)}"
        )
    L.append(
        f"- **Out of scope ({len(r.out_scope)} defs):** "
        f"{', '.join(f'`{d}`' for d in r.out_scope)}\n"
    )

    L.append("## 2. Structural correspondence (gap table)\n")
    L.append("| Reference def | LinkML def | Aspect | Class | Detail | Justification |")
    L.append("|---|---|---|---|---|---|")
    order = {REFINEMENT: 0, LOOSER: 1, UNMAPPED: 2, EQUIVALENT: 3, OUT_OF_SCOPE: 4}
    for g in sorted(r.gaps, key=lambda x: (order.get(x.classification, 9), x.ref_def)):
        if g.classification == OUT_OF_SCOPE:
            continue  # summarised above; keep the table focused on in-scope deltas
        L.append(
            f"| `{g.ref_def}` | `{g.linkml_def}` | {g.aspect} | **{g.classification}** "
            f"| {g.detail} | {g.justification} |"
        )
    n_oos = sum(1 for g in r.gaps if g.classification == OUT_OF_SCOPE)
    L.append(
        f"\n_{n_oos} OUT_OF_SCOPE definitions omitted from the table (listed in §1)._\n"
    )

    def bucket_block(title: str, b: Buckets) -> None:
        L.append(f"### {title}\n")
        L.append(f"- corpus size: **{b.total}**")
        L.append(f"- AGREE (both accept): {b.agree_accept}")
        L.append(f"- AGREE (both reject): {b.agree_reject}")
        L.append(
            f"- LINKML-STRICTER (A accept / L reject): {len(b.linkml_stricter)}"
            f" — expected (Δ refinements)"
        )
        breakdown = b.looseness_breakdown()
        bd = ", ".join(f"{k}={v}" for k, v in sorted(breakdown.items())) or "none"
        L.append(
            f"- disclosed looser (A reject / L accept, declared benign): "
            f"{len(b.disclosed_looser)} [{bd}]"
        )
        flag = (
            "✅ empty"
            if not b.linkml_looser
            else f"❌ {len(b.linkml_looser)} — REFUTES SOUNDNESS"
        )
        L.append(f"- **UNDISCLOSED LINKML-LOOSER (A reject / L accept): {flag}**")
        for s in b.linkml_looser[:10]:
            L.append(f"    - `{s['case']}` — {s.get('why', '')}")
        if b.errors:
            L.append(f"- ❌ instances the oracle could not validate: {len(b.errors)}")
        L.append("")

    sizes = r.corpus_sizes
    L.append("## 3. Differential oracle\n")
    L.append(
        f"Corpus: {sizes['seeds']} seed(s), {sizes['mutations']} mutation(s) of them, "
        f"{sizes['hypothesis_soundness']} instances generated from L and "
        f"{sizes['hypothesis_completeness']} from A|τ by `hypothesis-jsonschema`.\n"
    )
    bucket_block(
        "3a. Soundness corpus (L-grammar + mutations → must be A-valid)", r.soundness
    )
    bucket_block(
        "3b. Completeness corpus (A|τ-valid → measure L strictness)", r.completeness
    )

    L.append("## 4. Declared relaxations (Λ)\n")
    if not allowed:
        L.append("None declared: the proof is strict.\n")
    else:
        L.append(
            "Every declared location must be needed by at least one instance; "
            "the instance counts are per location.\n"
        )
        L.append("| Category | Allowed at | Instances | Why |")
        L.append("|---|---|---|---|")
        hits: dict[str, int] = {}
        for b in (r.soundness, r.completeness):
            for k, v in b.declaration_hits().items():
                hits[k] = hits.get(k, 0) + v
        for category, rule in sorted(allowed.items()):
            why = (justifications or {}).get(category, "")
            for declaration in rule.declarations:
                where = declaration.split(" @ ", 1)[1]
                shown = f"`$ref` into `{where}*`" if rule.marker else f"`{where}`"
                n = hits.get(declaration, 0)
                L.append(f"| `{category}` | {shown} | {n if n else '❌ 0'} | {why} |")
                why = "〃"
        L.append("")

    L.append("## 5. Result\n")
    L.append(
        f"- Corpus gate (differential oracle actually ran): "
        f"{'❌ FAIL — empty corpus, nothing was tested' if r.vacuous else '✅ PASS'}"
    )
    L.append(
        f"- Oracle gate (every instance validated): "
        f"{'✅ PASS' if not r.oracle_errors else f'❌ FAIL — {len(r.oracle_errors)} error(s)'}"
    )
    L.append(
        f"- Soundness gate (no undisclosed LINKML-LOOSER): "
        f"{'⚠️ VACUOUS — empty corpus' if r.vacuous else ('✅ PASS' if not r.soundness.linkml_looser else '❌ FAIL')}"
    )
    L.append(
        f"- Coverage gate (no UNMAPPED in-scope defs): "
        f"{'✅ PASS' if not r.unmapped else '❌ FAIL ' + str(r.unmapped)}"
    )
    L.append(
        f"- Structural gate (no LOOSER gap rows): "
        f"{'✅ PASS' if not r.structural_looser else f'❌ FAIL — {len(r.structural_looser)} row(s)'}"
    )
    L.append(
        f"- Declared relaxations no instance needed: "
        f"{'none ✅' if not r.unobserved_relaxations else ', '.join(r.unobserved_relaxations) + ' ❌'}"
    )
    observed = sorted({d.split(" @ ", 1)[0] for d in r.observed_relaxations})
    lam = ", ".join(observed) if observed else "∅ (strict refinement)"
    L.append(
        "\n> **Interpretation.** The relation proven is L = A|τ refined by Δ "
        "(intended strengthenings: vocabulary enums, required fields, closed "
        f"objects, const pins) and relaxed by the declared, bounded set Λ = {{{lam}}}. "
        "Λ is finite and every relaxation in it is bound to the locations in §4, so "
        "the claim is falsifiable: any instance L accepts that A rejects for a reason "
        "or at a location outside Λ appears in the UNDISCLOSED bucket and fails the "
        "gate. Δ is listed in §2 for the definitions both schemas share; strictness "
        "beyond them (map keys, the labelling sections) shows up only as the "
        "LINKML-STRICTER counts of §3.\n"
    )
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--spec", required=True, type=Path, help="per-migration proof spec (YAML)"
    )
    ap.add_argument("--out", type=Path, help="write the Markdown report here")
    ap.add_argument(
        "--root", type=Path, default=Path.cwd(), help="repo root for relative paths"
    )
    args = ap.parse_args(argv)
    configure_cli_logging()

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    report = prove(spec, args.root.resolve())
    md = report_markdown(
        report,
        parse_relaxations(spec.get("allow_looseness")),
        spec.get("justifications", {}),
    )

    if args.out:
        args.out.write_text(md, encoding="utf-8")
        logger.info("wrote %s", args.out)
    else:
        print(md)

    if report.vacuous:
        logger.error(
            "%s: differential corpus is EMPTY -- nothing was validated, so the "
            "soundness gate proves nothing. Check that the `seeds` globs in %s "
            "resolve relative to --root (%s).",
            report.name,
            args.spec,
            args.root.resolve(),
        )

    return 0 if report.passes else 1


if __name__ == "__main__":
    raise SystemExit(main())
