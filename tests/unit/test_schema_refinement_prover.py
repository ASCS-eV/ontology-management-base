"""Unit tests for the refinement prover's own mechanics.

These run on small synthetic schemas, so they need no submodule and run in every
test job. The proof over the real OpenLABEL schemas is gated separately, in
tests/unit/test_schema_refinement.py.
"""

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import schema_refinement_prover as prover  # noqa: E402

UID = "^[0-9]+$"

# A: the reference. `items` and `extra` are UID-keyed maps, inlined in `root` as
# ASAM inlines `tags`; `extra` entries require a `kind`, which L deliberately
# leaves unchecked.
REFERENCE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["root"],
    "properties": {"root": {"$ref": "#/definitions/root"}},
    "definitions": {
        "root": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "patternProperties": {UID: {"$ref": "#/definitions/item"}},
                },
                "extra": {"$ref": "#/definitions/extra"},
                "meta": {"$ref": "#/definitions/meta"},
            },
        },
        "item": {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "extra": {
            "type": "object",
            "additionalProperties": False,
            "patternProperties": {UID: {"type": "object", "required": ["kind"]}},
        },
        "meta": {"type": "object", "properties": {"label": {"type": "string"}}},
        "unused": {"type": "object"},
    },
}

# L: a LinkML-shaped refinement with an Unchecked* passthrough for `extra`.
LINKML = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["root"],
    "properties": {"root": {"$ref": "#/$defs/Root"}},
    "$defs": {
        "Root": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "items": {
                    "type": "object",
                    "propertyNames": {"pattern": UID},
                    "additionalProperties": {"$ref": "#/$defs/Item"},
                },
                "extra": {
                    "type": "object",
                    "propertyNames": {"pattern": UID},
                    "additionalProperties": {"$ref": "#/$defs/UncheckedEntry"},
                },
                "meta": {"$ref": "#/$defs/Meta"},
            },
        },
        "Item": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "UncheckedEntry": {"type": "object", "additionalProperties": True},
        "Meta": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"label": {"type": "string"}},
        },
    },
}

SEED = {"root": {"items": {"0": {"name": "a"}}, "meta": {"label": "x"}}}

UNCHECKED = {"unchecked_section": {"marker": "#/$defs/Unchecked"}}


def _errors(instance: dict) -> list:
    return list(prover.make_validator(REFERENCE).iter_errors(instance))


def _classify(instance: dict, allow_looseness: dict) -> set[str] | None:
    allowed = prover.parse_relaxations(allow_looseness)
    refs = prover._Refs(LINKML)
    return prover.categorize_looseness(_errors(instance), allowed, LINKML, refs)


# -- relaxation declarations --------------------------------------------------


def test_parse_relaxations_absent_is_strict() -> None:
    assert prover.parse_relaxations(None) == {}
    assert prover.parse_relaxations({}) == {}


@pytest.mark.parametrize(
    "cfg",
    [
        ["null_optional"],  # a list names no location, so it bounds nothing
        {"null_optional": {}},
        {"null_optional": {"paths": []}},
        {"unchecked_section": {}},
        {"no_such_category": {"paths": ["*"]}},
    ],
)
def test_parse_relaxations_rejects_unbounded_or_unknown(cfg) -> None:
    with pytest.raises(ValueError):
        prover.parse_relaxations(cfg)


# -- classification ----------------------------------------------------------


def test_classify_null_only_where_declared() -> None:
    doc = {"root": {"meta": {"label": None}}}
    declared_elsewhere = {"null_optional": {"paths": ["root.items.*"]}}
    declared_here = {"null_optional": {"paths": ["root.meta.label"]}}
    assert _classify(doc, declared_elsewhere) is None
    assert _classify(doc, declared_here) == {"null_optional @ root.meta.label"}


def test_classify_unchecked_content_below_the_marker() -> None:
    # A requires `kind` in every extra entry; L hands the entry to UncheckedEntry.
    assert _classify({"root": {"extra": {"0": {}}}}, UNCHECKED) == {
        "unchecked_section @ #/$defs/Unchecked"
    }


def test_classify_unchecked_does_not_cover_the_entry_type() -> None:
    # The passthrough definition is typed, so a wrong type at the anchor itself
    # is not content L declared it would skip.
    assert _classify({"root": {"extra": {"0": 5}}}, UNCHECKED) is None


def test_classify_unchecked_does_not_cover_keys() -> None:
    # The key is checked one level above the anchor: still L's business.
    assert _classify({"root": {"extra": {"x": {"kind": 1}}}}, UNCHECKED) is None


# -- references and scope ----------------------------------------------------


def test_refs_reject_a_pointer_into_a_definition() -> None:
    refs = prover._Refs(REFERENCE)
    assert refs.def_name("#/definitions/item") == "item"
    with pytest.raises(ValueError):
        refs.def_name("#/definitions/root/properties/items")


def test_project_scope_is_the_ref_closure() -> None:
    in_scope, out_scope = prover.project_scope(REFERENCE, ["root.items"])
    assert in_scope == {"item"}
    assert out_scope == {"root", "extra", "meta", "unused"}
    assert prover.spine_defs(REFERENCE, ["root.items"]) == {"root"}


def test_project_scope_rejects_an_unresolved_path() -> None:
    with pytest.raises(ValueError):
        prover.project_scope(REFERENCE, ["root.nope"])


# -- corpus ------------------------------------------------------------------


def test_mutation_corpus_reaches_uid_keyed_members() -> None:
    names = [name for name, _ in prover.mutation_corpus([SEED])]
    under_uid = [n for n in names if "['items']['0']" in n]
    assert any(":drop:" in n for n in under_uid)
    assert any(":swap:" in n and "['name']" in n for n in under_uid)
    assert any(":rekey:" in n for n in under_uid)


def test_mutation_corpus_rekey_keeps_the_value() -> None:
    corpus = dict(prover.mutation_corpus([SEED]))
    doc = corpus["seed0:rekey:$['root']['items']['0']"]
    assert doc["root"]["items"] == {prover._BAD_KEY: {"name": "a"}}


def test_hypothesis_corpus_fails_on_a_short_corpus() -> None:
    with pytest.raises(RuntimeError):
        prover.hypothesis_corpus({"const": 1}, 5)


# -- reporting ---------------------------------------------------------------


def test_justification_matches_whole_segments() -> None:
    configured = {"tag.required": "stricter", "type.enum": "vocabulary"}
    assert prover._justification(configured, "tag", "required", "x") == "stricter"
    assert prover._justification(configured, "tag", "type.enum", "x") == "vocabulary"
    assert (
        prover._justification(configured, "tag", "required_dropped", prover.LOOSER)
        != "stricter"
    )


def _report(**overrides) -> prover.ProofReport:
    fields = dict(
        name="t",
        in_scope=[],
        out_scope=[],
        gaps=[],
        soundness=prover.Buckets(agree_accept=1),
        completeness=prover.Buckets(),
        corpus_sizes={},
        unmapped=[],
    )
    fields.update(overrides)
    return prover.ProofReport(**fields)


def test_report_flags_a_declaration_nothing_needed() -> None:
    report = _report(declared=["null_optional @ root.items.*"])
    assert report.unobserved_relaxations == ["null_optional @ root.items.*"]
    assert report.sound
    assert not report.passes
    assert "STALE" in report.verdict()


def test_report_oracle_errors_break_soundness() -> None:
    assert _report().sound
    assert not _report(soundness=prover.Buckets(agree_accept=1, errors=["x"])).sound


# -- end to end on the synthetic pair -----------------------------------------


def _write_pair(tmp_path: Path, linkml: dict, allow: dict) -> dict:
    (tmp_path / "ref.json").write_text(json.dumps(REFERENCE))
    (tmp_path / "l.json").write_text(json.dumps(linkml))
    (tmp_path / "seed.json").write_text(json.dumps(SEED))
    return {
        "name": "synthetic",
        "reference_schema": "ref.json",
        "linkml_schema": "l.json",
        "scope_keep": ["root.items", "root.meta"],
        "def_map": {"item": "Item", "meta": "Meta"},
        "hypothesis": {"soundness": 30, "completeness": 30},
        "allow_looseness": allow,
        "seeds": ["seed.json"],
    }


def test_prove_accepts_a_sound_refinement(tmp_path: Path) -> None:
    report = prover.prove(_write_pair(tmp_path, LINKML, UNCHECKED), tmp_path)
    assert report.sound, report.soundness.linkml_looser[:3]
    assert report.unobserved_relaxations == []


def test_prove_refutes_a_dropped_key_constraint(tmp_path: Path) -> None:
    loose = json.loads(json.dumps(LINKML))
    del loose["$defs"]["Root"]["properties"]["items"]["propertyNames"]
    report = prover.prove(_write_pair(tmp_path, loose, UNCHECKED), tmp_path)
    assert not report.sound
    assert any(":rekey:" in c["case"] for c in report.soundness.linkml_looser)


def test_reference_and_linkml_fixtures_are_valid_schemas() -> None:
    for schema in (REFERENCE, LINKML):
        jsonschema.validators.validator_for(schema).check_schema(schema)


# -- unchecked locations, projection, gap table, corpus ---------------------------


def _depth(schema: dict, location: tuple) -> int | None:
    return prover._unchecked_depth(
        schema, location, "#/$defs/Unchecked", prover._Refs(schema)
    )


def _wrap(extra_schema: dict) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"extra": extra_schema},
        "$defs": {
            "UncheckedEntry": {"type": "object", "additionalProperties": True},
            "Strict": {"type": "object", "required": ["kind"]},
        },
    }


def test_unchecked_through_any_branch_of_anyof() -> None:
    schema = _wrap({"anyOf": [{"$ref": "#/$defs/UncheckedEntry"}, {"type": "null"}]})
    assert _depth(schema, ("extra", "kind")) == 1


def test_allof_with_a_checked_branch_is_not_unchecked() -> None:
    schema = _wrap(
        {"allOf": [{"$ref": "#/$defs/UncheckedEntry"}, {"$ref": "#/$defs/Strict"}]}
    )
    assert _depth(schema, ("extra", "kind")) is None


def test_ref_with_constraining_siblings_is_not_unchecked() -> None:
    schema = _wrap({"$ref": "#/$defs/UncheckedEntry", "required": ["kind"]})
    assert _depth(schema, ("extra", "kind")) is None
    annotated = _wrap({"$ref": "#/$defs/UncheckedEntry", "description": "x"})
    assert _depth(annotated, ("extra", "kind")) == 1


def test_unchecked_walk_follows_pattern_properties() -> None:
    schema = _wrap(
        {
            "type": "object",
            "patternProperties": {"^[0-9]+$": {"$ref": "#/$defs/UncheckedEntry"}},
        }
    )
    assert _depth(schema, ("extra", "0", "kind")) == 2
    assert _depth(schema, ("extra", "x", "kind")) is None


def test_projection_follows_refs_and_keeps_the_reference_intact() -> None:
    projected = prover.build_projected_schema(REFERENCE, ["root.items"])
    root = projected["properties"]["root"]
    assert set(root["properties"]) == {"items"}
    assert set(projected["definitions"]) == {"item"}
    assert set(REFERENCE["definitions"]["root"]["properties"]) == {
        "items",
        "extra",
        "meta",
    }


def test_object_view_enters_map_entries_and_object_branches() -> None:
    schema = {
        "definitions": {
            "map": {
                "type": "object",
                "patternProperties": {UID: {"$ref": "#/definitions/entry"}},
            },
            "entry": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "required": ["uri"],
                        "additionalProperties": False,
                    },
                ]
            },
        }
    }
    view = prover._object_view(schema, {"$ref": "#/definitions/map"})
    assert view["required"] == ["uri"] and view["additionalProperties"] is False


def test_structural_gaps_skip_string_valued_maps() -> None:
    ref = {
        "definitions": {
            "names": {"type": "object", "patternProperties": {UID: {"type": "string"}}}
        }
    }
    linkml = {
        "$defs": {
            "Name": {
                "type": "object",
                "required": ["value"],
                "additionalProperties": False,
                "properties": {"value": {"type": "string"}},
            }
        }
    }
    rows, unmapped = prover.structural_gaps(
        ref, linkml, {"names"}, set(), {"names": "Name"}, lambda *a: ""
    )
    assert rows == [] and unmapped == []


def test_mutation_corpus_swaps_containers_but_not_for_themselves() -> None:
    corpus = dict(prover.mutation_corpus([{"a": {"b": 1}, "c": True}]))
    assert corpus["seed0:swap:$['a']=None"] == {"a": None, "c": True}
    assert "seed0:swap:$['a']={}" in corpus  # {} differs from {"b": 1}
    assert "seed0:swap:$['c']=True" not in corpus  # identical to the seed
    assert "seed0:swap:$['a']['b']=True" in corpus  # True is not the integer 1


def test_prove_rejects_a_seed_glob_that_matches_nothing(tmp_path: Path) -> None:
    spec = _write_pair(tmp_path, LINKML, UNCHECKED)
    spec["seeds"] = ["typo/*.json"]
    with pytest.raises(ValueError):
        prover.prove(spec, tmp_path)


_GENERATE = """
import json, sys
{preload}
sys.path.insert(0, {scripts!r})
import schema_refinement_prover as prover
print(json.dumps(prover.hypothesis_corpus(json.loads(sys.argv[1]), 30)))
"""


def _corpus_from_a_fresh_process(preload: str) -> list:
    code = _GENERATE.format(preload=preload, scripts=str(ROOT_DIR / "scripts"))
    result = subprocess.run(
        [sys.executable, "-c", code, json.dumps(LINKML)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        check=True,
    )
    return json.loads(result.stdout)


def test_hypothesis_corpus_does_not_depend_on_the_calling_process() -> None:
    """Hypothesis mixes constants from the local modules loaded in its process
    into generation. Generated in-process, these two callers got different
    corpora; through the worker they must get the same one."""
    bare = _corpus_from_a_fresh_process("")
    loaded = _corpus_from_a_fresh_process("import omb.api, omb.core.negative_fixtures")
    assert bare == loaded


def test_unchecked_needs_nothing_else_constraining_the_location() -> None:
    anyof_with_sibling = _wrap(
        {
            "properties": {"kind": {"type": "string"}},
            "anyOf": [{"$ref": "#/$defs/UncheckedEntry"}],
        }
    )
    assert _depth(anyof_with_sibling, ("extra", "kind")) is None
    chain = _wrap({"$ref": "#/$defs/Wrapper", "required": ["kind"]})
    chain["$defs"]["Wrapper"] = {"$ref": "#/$defs/UncheckedEntry"}
    assert _depth(chain, ("extra", "kind")) is None


def test_unchecked_requires_every_applicable_subschema() -> None:
    two_patterns = _wrap(
        {
            "type": "object",
            "patternProperties": {
                "^[0-9]+$": {"$ref": "#/$defs/UncheckedEntry"},
                "^0$": {"$ref": "#/$defs/Strict"},
            },
        }
    )
    assert _depth(two_patterns, ("extra", "0", "kind")) is None
    assert _depth(two_patterns, ("extra", "7", "kind")) == 2
    named_and_pattern = _wrap(
        {
            "type": "object",
            "properties": {"0": {"$ref": "#/$defs/Strict"}},
            "patternProperties": {"^[0-9]+$": {"$ref": "#/$defs/UncheckedEntry"}},
        }
    )
    assert _depth(named_and_pattern, ("extra", "0", "kind")) is None


def test_completeness_counterexamples_break_soundness() -> None:
    bad = prover.Buckets(linkml_looser=[{"case": "hypA0", "why": "x"}])
    assert not _report(completeness=bad).sound


def test_projection_follows_a_chain_of_refs() -> None:
    schema = {
        "type": "object",
        "properties": {"r": {"$ref": "#/definitions/a"}},
        "definitions": {
            "a": {"$ref": "#/definitions/b"},
            "b": {
                "type": "object",
                "properties": {"keep": {"type": "string"}, "drop": {"type": "string"}},
            },
        },
    }
    projected = prover.build_projected_schema(schema, ["r.keep"])
    assert set(projected["properties"]["r"]["properties"]) == {"keep"}
    assert set(schema["definitions"]["b"]["properties"]) == {"keep", "drop"}


def test_strip_properties_forbids_instead_of_deleting() -> None:
    open_object = {"type": "object", "properties": {"attributes": {"type": "object"}}}
    stripped = prover.strip_properties(open_object, ["attributes"])
    assert stripped["properties"]["attributes"] is False
    assert all("attributes" not in x for x in prover.hypothesis_corpus(stripped, 25))


def test_gap_table_reports_members_only_l_constrains() -> None:
    ref = {"definitions": {"meta": {"type": "object", "properties": {}}}}
    linkml = {
        "$defs": {
            "Meta": {
                "type": "object",
                "properties": {"tagged_file": {"type": "string"}},
            }
        }
    }
    rows, _ = prover.structural_gaps(
        ref, linkml, {"meta"}, set(), {"meta": "Meta"}, lambda *a: ""
    )
    assert [(g.aspect, g.classification) for g in rows] == [
        ("members only L constrains", prover.REFINEMENT)
    ]
    ref["definitions"]["meta"]["additionalProperties"] = False
    rows, _ = prover.structural_gaps(
        ref, linkml, {"meta"}, set(), {"meta": "Meta"}, lambda *a: ""
    )
    assert [(g.aspect, g.classification) for g in rows] == [
        ("members A forbids", prover.LOOSER)
    ]
