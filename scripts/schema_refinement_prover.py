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

    Soundness     : for all x. L accepts x  =>  A accepts x
                    (everything L calls valid, A also calls valid -- L never
                    invents a format A forbids). One counterexample refutes it.
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

    python scripts/schema_refinement_prover.py --spec linkml/openlabel-v2/proof_spec.yaml
    python scripts/schema_refinement_prover.py --spec <spec> --out REFINEMENT_PROOF.md
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml

try:  # local style: centralized logging when available
    from src.tools.core.logging import get_logger

    logger = get_logger(__name__)
except Exception:  # pragma: no cover - standalone fallback
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    logger = logging.getLogger(__name__)

# hypothesis-jsonschema is optional. Without it the mutation corpus still runs
# (and the soundness gate still has teeth); the property-based completeness
# sampling is skipped with a warning.
try:
    import hypothesis
    from hypothesis import HealthCheck, settings
    from hypothesis_jsonschema import from_schema

    _HAS_HYPOTHESIS = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_HYPOTHESIS = False


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
    category: str = ""  # for LOOSER rows: which declared looseness class


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
        counts: dict[str, int] = {}
        for s in self.disclosed_looser:
            for c in s["categories"]:
                counts[c] = counts.get(c, 0) + 1
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

    @property
    def structural_looser(self) -> list[GapRow]:
        return [g for g in self.gaps if g.classification == LOOSER]

    @property
    def undisclosed_structural_looser(self) -> list[GapRow]:
        """LOOSER schema rows whose looseness is NOT a declared category."""
        return [g for g in self.structural_looser if not g.category]

    @property
    def sound(self) -> bool:
        """No UNDISCLOSED way for L to accept what A rejects, and no in-scope
        definition left unmodelled. Disclosed, justified relaxations (declared
        in the spec's allow_looseness) do not break the relation."""
        return (
            len(self.soundness.linkml_looser) == 0
            and not self.undisclosed_structural_looser
            and not self.unmapped
        )

    def verdict(self) -> str:
        return (
            "PROVEN (sound refinement modulo declared relaxations)"
            if self.sound
            else "REFUTED"
        )


# =============================================================================
# Pillar 1 -- scope projection ($ref reachability)
# =============================================================================


def _defs_key(schema: dict) -> str:
    """Return whichever definitions container the schema uses."""
    if "definitions" in schema:
        return "definitions"
    return "$defs"


def _collect_refs(node: Any, acc: set[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str):
                acc.add(v.split("/")[-1])
            else:
                _collect_refs(v, acc)
    elif isinstance(node, list):
        for item in node:
            _collect_refs(item, acc)


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
    """Follow a single top-level $ref into the schema's definitions."""
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 16:
        name = node["$ref"].split("/")[-1]
        node = schema.get(_defs_key(schema), {}).get(name, {})
        seen += 1
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

    reach: set[str] = set()
    for path in keep_paths:
        node = _navigate(schema, path)
        if node is None:
            logger.warning("scope path %r did not resolve; ignored", path)
            continue
        _collect_refs(node, reach)

    frontier = set(reach)
    while frontier:
        nxt: set[str] = set()
        for d in frontier:
            _collect_refs(schema.get(dk, {}).get(d, {}), nxt)
        nxt -= reach
        reach |= nxt
        frontier = nxt

    in_scope = reach & all_defs
    return in_scope, all_defs - in_scope


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

    def prune(node: Any, sub: dict) -> None:
        if not isinstance(node, dict) or not sub:
            return  # leaf of the keep-trie: retain node entirely
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

    # Keep exactly the defs still reachable from the pruned root (this includes
    # spine defs such as 'openlabel' itself, not just the leaf-reachable set).
    reach = _reachable_from_root(proj)
    proj[dk] = {k: v for k, v in proj.get(dk, {}).items() if k in reach}
    return proj


def _reachable_from_root(schema: dict) -> set[str]:
    """All definition names reachable by $ref from the schema root."""
    dk = _defs_key(schema)
    reach: set[str] = set()
    _collect_refs({k: v for k, v in schema.items() if k != dk}, reach)
    frontier = set(reach)
    while frontier:
        nxt: set[str] = set()
        for d in frontier:
            _collect_refs(schema.get(dk, {}).get(d, {}), nxt)
        nxt -= reach
        reach |= nxt
        frontier = nxt
    return reach


def strip_properties(schema: dict, names: list[str]) -> dict:
    """Return a copy with the named (optional) properties removed everywhere.

    Used to break recursive cycles for property-based generation: every pruned
    property is optional, so generated instances remain valid against the full
    schema -- generation simply never populates that subtree."""
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
                        del props[nm]
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
# is only treated as benign when the spec's allow_looseness declares it.
KEY_PATTERN = "key_pattern"  # A constrains dict keys; L accepts any key
NULL_OPTIONAL = "null_optional"  # L permits explicit JSON null where A forbids it
# L permits the object form of a LinkML inlined simple-dict value (an object with
# the value slot) where A allows only the bare scalar. This is a LinkML
# expressivity limit: an inlined simple-dict cannot be restricted to scalar-only
# values, so the object form is always accepted.
SIMPLE_DICT_OBJECT_FORM = "simple_dict_object_form"


def _expects_scalar(validator_value: Any) -> bool:
    """True if a JSON Schema ``type`` keyword value names a scalar type."""
    scalars = {"string", "number", "integer", "boolean"}
    if isinstance(validator_value, str):
        return validator_value in scalars
    if isinstance(validator_value, list):
        return any(t in scalars for t in validator_value)
    return False


def categorize_looseness(errors: list, allowed: set[str]) -> set[str] | None:
    """Classify why A rejected an instance L accepted.

    Returns the set of looseness categories iff EVERY reference-schema error
    falls into a *declared-allowed* category (benign, disclosed looseness).
    Returns None if any error is outside the allowed categories -- i.e. a real,
    undisclosed soundness violation."""
    cats: set[str] = set()
    for e in errors:
        if e.validator in ("additionalProperties", "patternProperties"):
            cat = KEY_PATTERN
        elif e.validator == "type" and e.instance is None:
            cat = NULL_OPTIONAL
        elif (
            e.validator == "type"
            and isinstance(e.instance, dict)
            and _expects_scalar(e.validator_value)
        ):
            cat = SIMPLE_DICT_OBJECT_FORM
        else:
            return None  # undisclosed looseness
        if cat not in allowed:
            return None
        cats.add(cat)
    return cats


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


def structural_gaps(
    ref: dict,
    linkml: dict,
    in_scope: set[str],
    out_scope: set[str],
    mapping: dict[str, str | None],
    justifier,
    allowed: set[str],
) -> tuple[list[GapRow], list[str]]:
    """Emit classified gap rows for every in-scope def + every out-of-scope def.
    Returns (rows, unmapped_in_scope_defs)."""
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
                "not modelled",
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

        rdef = _resolve_ref(ref, ref.get(rdk, {}).get(rd, {}))
        ldef = _resolve_ref(linkml, linkml.get(ldk, {}).get(ld, {}))
        if not isinstance(rdef, dict) or not isinstance(ldef, dict):
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
        # key-pattern looseness: A restricts keys, L accepts any key
        if rdef.get("patternProperties") and isinstance(l_add, dict):
            rows.append(
                GapRow(
                    rd,
                    ld,
                    "key-pattern",
                    LOOSER,
                    "A constrains dict keys via patternProperties; "
                    "L accepts any key (additionalProperties)",
                    justifier(rd, "key_pattern", LOOSER),
                    category=KEY_PATTERN if KEY_PATTERN in allowed else "",
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
                    category=NULL_OPTIONAL if NULL_OPTIONAL in allowed else "",
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


def mutation_corpus(seeds: list[Any], cap_per_seed: int = 60) -> list[tuple[str, Any]]:
    """Deterministically derive malformed/edge instances from valid seeds:
    drop each required-ish key, type-swap each leaf, inject junk keys/values."""
    out: list[tuple[str, Any]] = []
    swaps = [None, "___JUNK___", 12345, 3.14, True, [], {}]

    def walk(node: Any, path: str, mutate):
        """Yield mutated copies by applying `mutate` at every json location."""
        if isinstance(node, dict):
            for k in list(node):
                yield from mutate(node, k, f"{path}.{k}")
                yield from walk(node[k], f"{path}.{k}", mutate)
        elif isinstance(node, list):
            for i, _ in enumerate(node):
                yield from walk(node[i], f"{path}[{i}]", mutate)

    for si, seed in enumerate(seeds):
        out.append((f"seed{si}", copy.deepcopy(seed)))

        # 1. drop each key
        def drop(parent, key, p):
            c = copy.deepcopy(seed)
            tgt = _follow(c, p)
            if tgt is not None:
                par, last = tgt
                del par[last]
                yield (f"seed{si}:drop:{p}", c)

        # 2. type-swap each leaf value
        def swap(parent, key, p):
            for s in swaps:
                c = copy.deepcopy(seed)
                tgt = _follow(c, p)
                if tgt is not None:
                    par, last = tgt
                    if not isinstance(par[last], (dict, list)):
                        par[last] = s
                        yield (f"seed{si}:swap:{p}={s!r}", c)

        # 3. inject a junk key at each object
        def inject(parent, key, p):
            c = copy.deepcopy(seed)
            tgt = _follow(c, p)
            if tgt is not None:
                par, last = tgt
                if isinstance(par[last], dict):
                    par[last]["___unexpected___"] = "x"
                    yield (f"seed{si}:inject:{p}", c)

        seen = 0
        for gen in (drop, swap, inject):
            for name, inst in walk(seed, "$", gen):
                out.append((name, inst))
                seen += 1
                if seen >= cap_per_seed:
                    break
            if seen >= cap_per_seed:
                break
    return out


def _follow(root: Any, dotted: str):
    """Resolve a '$.a.b[0]' path to (parent_container, last_key). None if absent."""
    parts = dotted.replace("[", ".").replace("]", "").split(".")[1:]
    node = root
    for part in parts[:-1]:
        key: Any = int(part) if part.isdigit() else part
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            return None
    last = parts[-1]
    last = int(last) if last.isdigit() else last
    try:
        node[last]
    except (KeyError, IndexError, TypeError):
        return None
    return node, last


def hypothesis_corpus(schema: dict, n: int) -> list[Any]:
    """Property-based instance generation from a (projected) schema."""
    if not _HAS_HYPOTHESIS or n <= 0:
        return []
    out: list[Any] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        strat = from_schema(schema)

        @settings(
            max_examples=n,
            deadline=None,
            database=None,
            derandomize=True,  # reproducible -> deterministic CI gate
            suppress_health_check=list(HealthCheck),
        )
        @hypothesis.given(strat)
        def collect(example):
            out.append(example)

        try:
            collect()
        except Exception as exc:  # generation can fail on exotic schemas
            logger.warning("hypothesis generation incomplete: %s", exc)
    return out


def differential(
    corpus: Iterable[tuple[str, Any]],
    ref_validator,
    linkml_validator,
    allowed: set[str],
) -> Buckets:
    b = Buckets()
    for name, inst in corpus:
        try:
            a_ok, a_err = validate(ref_validator, inst)
            l_ok, _ = validate(linkml_validator, inst)
        except Exception as exc:  # pragma: no cover
            b.errors.append(f"{name}: {exc}")
            continue
        if a_ok and l_ok:
            b.agree_accept += 1
        elif not a_ok and not l_ok:
            b.agree_reject += 1
        elif a_ok and not l_ok:
            b.linkml_stricter.append({"case": name})
        else:  # not a_ok and l_ok  -> L accepts what A rejects
            cats = categorize_looseness(a_err, allowed)
            if cats is None:
                b.linkml_looser.append(
                    {"case": name, "why": "; ".join(e.message for e in a_err[:2])}
                )
            else:
                b.disclosed_looser.append({"case": name, "categories": sorted(cats)})
    return b


# =============================================================================
# Orchestration
# =============================================================================


def _generate_linkml_schema(yaml_path: Path) -> dict:
    import subprocess

    res = subprocess.run(
        [sys.executable, "-m", "linkml.generators.jsonschemagen", str(yaml_path)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"jsonschemagen failed: {res.stderr}")
    return json.loads(res.stdout)


def prove(spec: dict, root: Path) -> ProofReport:
    name = spec.get("name", "migration")
    ref = json.loads((root / spec["reference_schema"]).read_text(encoding="utf-8"))

    if spec.get("linkml_schema"):
        linkml = json.loads((root / spec["linkml_schema"]).read_text(encoding="utf-8"))
    elif spec.get("linkml_yaml"):
        linkml = _generate_linkml_schema(root / spec["linkml_yaml"])
    else:
        raise ValueError("spec needs 'linkml_schema' or 'linkml_yaml'")

    keep = spec.get("scope_keep")
    in_scope, out_scope = project_scope(ref, keep)
    logger.info(
        "%s: %d in-scope defs, %d out-of-scope", name, len(in_scope), len(out_scope)
    )

    # justification lookup: substring match against spec.justifications
    just_cfg: dict[str, str] = spec.get("justifications", {})

    def justifier(ref_def: str, aspect_key: str, classification: str) -> str:
        key = f"{ref_def}.{aspect_key}"
        for pat, txt in just_cfg.items():
            if pat in key or pat == classification or pat == aspect_key:
                return txt
        return {
            OUT_OF_SCOPE: "Outside declared scope; unreachable from kept entry points.",
            REFINEMENT: "Intended strengthening (Delta): L validates what A leaves open.",
            LOOSER: "DISCLOSED looseness -- must be justified or fixed.",
            UNMAPPED: "GAP: in-scope definition without a LinkML counterpart.",
        }.get(classification, "")

    allowed = set(spec.get("allow_looseness", [KEY_PATTERN, NULL_OPTIONAL]))

    mapping = match_definitions(ref, linkml, in_scope, spec.get("def_map", {}))
    gaps, unmapped = structural_gaps(
        ref, linkml, in_scope, out_scope, mapping, justifier, allowed
    )

    ref_v = make_validator(ref)
    linkml_v = make_validator(linkml)

    # corpus
    seeds: list[Any] = []
    for g in spec.get("seeds", []):
        for p in sorted(root.glob(g)):
            seeds.append(json.loads(p.read_text(encoding="utf-8")))

    n_sound = int(spec.get("hypothesis", {}).get("soundness", 0))
    n_compl = int(spec.get("hypothesis", {}).get("completeness", 0))
    # Optional properties to drop for property-based GENERATION only, to break
    # recursive $ref cycles that hypothesis-jsonschema cannot expand. Pruned
    # subtrees are optional, so generated instances stay valid against the full
    # schema; the mutation corpus + seeds still exercise those subtrees.
    gen_prune = spec.get("generation_prune", [])

    # Soundness corpus: instances drawn from L's own grammar (+ seeds) -> must be A-valid.
    sound_corpus: list[tuple[str, Any]] = list(mutation_corpus(seeds)) if seeds else []
    for i, inst in enumerate(
        hypothesis_corpus(strip_properties(linkml, gen_prune), n_sound)
    ):
        sound_corpus.append((f"hypL{i}", inst))

    # Completeness corpus: A|t-valid instances -> measure how much stricter L is.
    projected = build_projected_schema(ref, keep)
    compl_corpus: list[tuple[str, Any]] = [
        (f"hypA{i}", inst)
        for i, inst in enumerate(
            hypothesis_corpus(strip_properties(projected, gen_prune), n_compl)
        )
    ]
    for si, seed in enumerate(seeds):
        compl_corpus.append((f"seed{si}", seed))

    soundness = differential(sound_corpus, ref_v, linkml_v, allowed)
    completeness = differential(compl_corpus, ref_v, linkml_v, allowed)

    return ProofReport(
        name=name,
        in_scope=sorted(in_scope),
        out_scope=sorted(out_scope),
        gaps=gaps,
        soundness=soundness,
        completeness=completeness,
        corpus_sizes={
            "soundness": len(sound_corpus),
            "completeness": len(compl_corpus),
            "seeds": len(seeds),
            "hypothesis_available": int(_HAS_HYPOTHESIS),
        },
        unmapped=unmapped,
    )


# =============================================================================
# Reporting
# =============================================================================


def report_markdown(r: ProofReport) -> str:
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

    def bucket_block(title: str, b: Buckets, *, gate: bool) -> None:
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
        if b.linkml_looser:
            for s in b.linkml_looser[:10]:
                L.append(f"    - `{s['case']}` — {s.get('why', '')}")
        if b.errors:
            L.append(f"- generation/validation errors: {len(b.errors)}")
        L.append("")

    L.append("## 3. Differential oracle\n")
    bucket_block(
        "3a. Soundness corpus (L-grammar + mutations → must be A-valid)",
        r.soundness,
        gate=True,
    )
    bucket_block(
        "3b. Completeness corpus (A|τ-valid → measure L strictness)",
        r.completeness,
        gate=False,
    )

    if not r.corpus_sizes.get("hypothesis_available"):
        L.append(
            "> ⚠️ `hypothesis-jsonschema` not installed — property-based "
            "generation skipped; only the mutation corpus ran.\n"
        )

    L.append("## 4. Result\n")
    L.append(
        f"- Soundness gate (no undisclosed LINKML-LOOSER): "
        f"{'✅ PASS' if not r.soundness.linkml_looser else '❌ FAIL'}"
    )
    L.append(
        f"- Coverage gate (no UNMAPPED in-scope defs): "
        f"{'✅ PASS' if not r.unmapped else '❌ FAIL ' + str(r.unmapped)}"
    )
    L.append(
        f"- Structural LOOSER rows: {len(r.structural_looser)} total, "
        f"{len(r.undisclosed_structural_looser)} undisclosed "
        f"{'✅' if not r.undisclosed_structural_looser else '❌'}"
    )
    observed = sorted(
        set(r.soundness.looseness_breakdown())
        | set(r.completeness.looseness_breakdown())
    )
    lam = ", ".join(observed) if observed else "∅ (strict refinement)"
    L.append(
        "\n> **Interpretation.** The relation proven is L = A|τ refined by Δ "
        "(intended strengthenings: vocabulary enums, required fields, closed "
        f"objects, const pins) and relaxed by the declared, bounded set Λ = {{{lam}}}. "
        "Both Δ and Λ are finite and enumerated here, so the claim is falsifiable: "
        "any instance L accepts that A rejects for a reason outside Λ appears in "
        "the UNDISCLOSED bucket and fails the gate.\n"
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

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    report = prove(spec, args.root.resolve())
    md = report_markdown(report)

    if args.out:
        args.out.write_text(md, encoding="utf-8")
        logger.info("wrote %s", args.out)
    else:
        print(md)

    return 0 if report.sound else 1


if __name__ == "__main__":
    raise SystemExit(main())
