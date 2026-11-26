#!/usr/bin/env python3
"""Tests for the OpenLABEL scenario-tagging structural schema.

Every assertion runs against the published artifact
(artifacts/openlabel-tagging/openlabel-tagging.schema.json), which is what
consumers get; CI's Generate Artifacts job separately keeps it in step with the
LinkML model.

Tests cover:
    1. Structure of the published JSON Schema
    2. Schema validation of spec examples (functional equivalence with ASAM)
    3. The generated TagTypeEnum and its faithfulness to the ASAM vocabulary
    4. The profile scope: validated sections and unchecked passthrough
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import rdflib
import yaml
from rdflib import URIRef
from rdflib.namespace import RDF, RDFS

from omb.core.constants import ASAM_SUBMODULE_HINT

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
SHIPPED_SCHEMA = (
    ROOT_DIR / "artifacts" / "openlabel-tagging" / "openlabel-tagging.schema.json"
)
TAG_TYPES_YAML = ROOT_DIR / "linkml" / "openlabel-tagging" / "tag-types.yaml"
SYNC_SCRIPT = ROOT_DIR / "scripts" / "sync_tag_type_enum.py"
# Authoritative ASAM OpenLABEL v1.0.0 JSON Schema (the format we claim parity with).
ASAM_SCHEMA = (
    ROOT_DIR
    / "submodules"
    / "asam-openx-standards"
    / "standards"
    / "asam-openlabel"
    / "schema"
    / "openlabel_json_schema-v1.0.0.json"
)
# Authoritative ASAM scenario tagging ontology (source of valid tag.type names).
ASAM_ONTOLOGY_TTL = (
    ROOT_DIR
    / "submodules"
    / "asam-openx-standards"
    / "standards"
    / "asam-openlabel"
    / "ontologies"
    / "openlabel_ontology_scenario_tags.ttl"
)


def _require_pinned_sources(path: Path, what: str) -> Path:
    """Return *path*, or skip locally / fail where the sources are guaranteed.

    The authoritative ASAM OpenLABEL schema and tagging ontology live in a ~260 MB
    submodule that the cheap test matrix deliberately does not check out, so skipping
    is right there. In the ``Pinned Standards Drift`` job, which initialises the
    submodule and sets ``OMB_REQUIRE_PINNED_SOURCES=1``, a missing file must fail
    instead: a conformance gate that quietly stops running is worse than no gate.
    """
    if path.exists():
        return path
    if os.environ.get("OMB_REQUIRE_PINNED_SOURCES"):
        raise AssertionError(
            f"{what} is missing while OMB_REQUIRE_PINNED_SOURCES is set. "
            f"{ASAM_SUBMODULE_HINT}"
        )
    pytest.skip(f"{what} not checked out. {ASAM_SUBMODULE_HINT}")


def _asam_ontology() -> rdflib.Graph:
    """The pinned ASAM scenario tagging ontology, or skip/fail per the rule."""
    path = _require_pinned_sources(
        ASAM_ONTOLOGY_TTL, "the pinned ASAM OpenLABEL tagging ontology"
    )
    return rdflib.Graph().parse(path)


def _local(term: rdflib.term.Node) -> str:
    return str(term).rsplit("/", 1)[-1]


# ASAM types its properties as rdfs:Property, a term RDFS does not define (the
# standard one is rdf:Property), so it has to be named explicitly.
ASAM_PROPERTY = URIRef(str(RDFS) + "Property")


def _asam_tag_classes() -> set[str]:
    """Local names of every rdfs:Class in the ASAM scenario tagging ontology."""
    return {_local(s) for s in _asam_ontology().subjects(RDF.type, RDFS.Class)}


def _asam_admin_properties() -> set[str]:
    """ASAM's administration tags: the Scenario properties other than hasTag,
    which links a scenario to its tags. Every other ASAM property is the value
    of a flag (its domain is that flag's class) and is not a tag type."""
    g = _asam_ontology()
    return {
        _local(s)
        for s in g.subjects(RDF.type, ASAM_PROPERTY)
        if _local(g.value(s, RDFS.domain)) == "Scenario" and _local(s) != "hasTag"
    }


def _tag_type_enum(schema: dict) -> list[str]:
    """Extract the TagTypeEnum permissible values from a generated JSON Schema."""
    return schema["$defs"]["TagTypeEnum"]["enum"]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def shipped_schema() -> dict:
    """The published JSON Schema, as consumers get it."""
    return json.loads(SHIPPED_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def asam_schema() -> dict:
    """Load the authoritative ASAM OpenLABEL v1.0.0 JSON Schema."""
    path = _require_pinned_sources(
        ASAM_SCHEMA, "the pinned ASAM OpenLABEL v1.0.0 JSON Schema"
    )
    return json.loads(path.read_text(encoding="utf-8"))


# =============================================================================
# Test instances (ASAM v1 format)
# =============================================================================

VALID_MINIMAL = {
    "openlabel": {
        "metadata": {"schema_version": "1.0.0"},
        "ontologies": {
            "0": {
                "uri": "https://openlabel.asam.net/V1-0-0/ontologies/openlabel_ontology_scenario_tags.ttl"
            }
        },
        "tags": {
            "0": {"type": "RoadTypeMinor", "ontology_uid": "0"},
            "1": {"type": "HorizontalStraights", "ontology_uid": "0"},
        },
    }
}

VALID_FULL_SCENARIO = {
    "openlabel": {
        "metadata": {
            "schema_version": "1.0.0",
            "tagged_file": "../resources/scenarios/scenario123.osc",
        },
        "ontologies": {
            "0": {
                "uri": "https://openlabel.asam.net/V1-0-0/ontologies/openlabel_ontology_scenario_tags.ttl",
                "boundary_list": [
                    "DrivableAreaSigns",
                    "DrivableAreaEdge",
                    "DrivableAreaSurface",
                ],
                "boundary_mode": "exclude",
            }
        },
        "tags": {
            "0": {"type": "RoadTypeMinor", "ontology_uid": "0"},
            "1": {"type": "HorizontalStraights", "ontology_uid": "0"},
            "3": {"type": "LaneTypeTraffic", "ontology_uid": "0"},
            "4": {"type": "ZoneSchool", "ontology_uid": "0"},
            "5": {"type": "IntersectionCrossroad", "ontology_uid": "0"},
            "7": {
                "type": "WeatherWind",
                "ontology_uid": "0",
                "tag_data": {"vec": [{"type": "range", "val": [10, 25]}]},
            },
            "11": {"type": "VehicleCar", "ontology_uid": "0"},
            "13": {"type": "MotionDrive", "ontology_uid": "0"},
            "15": {
                "type": "scenarioUniqueReference",
                "ontology_uid": "0",
                "tag_data": {"text": [{"type": "value", "val": "c133241e-f325-11eb"}]},
            },
        },
    }
}

VALID_NUMERIC = {
    "openlabel": {
        "metadata": {"schema_version": "1.0.0"},
        "ontologies": {
            "0": {"uri": "https://openlabel.asam.net/V1-0-0/ontologies/openlabel.ttl"}
        },
        "tags": {
            "0": {
                "type": "WeatherRain",
                "ontology_uid": "0",
                "tag_data": {"num": [{"type": "value", "val": 3.1}]},
            }
        },
    }
}

INVALID_NO_METADATA = {
    "openlabel": {"tags": {"0": {"type": "WeatherRain", "ontology_uid": "0"}}}
}

INVALID_NO_TAG_TYPE = {
    "openlabel": {
        "metadata": {"schema_version": "1.0.0"},
        "tags": {"0": {"ontology_uid": "0"}},
    }
}

INVALID_WRONG_TAG_TYPE = {
    "openlabel": {
        "metadata": {"schema_version": "1.0.0"},
        "ontologies": {"0": {"uri": "https://example.org/ont"}},
        "tags": {"0": {"type": "CompletelyFakeTag", "ontology_uid": "0"}},
    }
}

INVALID_WRONG_BOUNDARY_MODE = {
    "openlabel": {
        "metadata": {"schema_version": "1.0.0"},
        "ontologies": {
            "0": {"uri": "https://x.org/o", "boundary_mode": "something_invalid"}
        },
        "tags": {},
    }
}

INVALID_NUM_VAL_STRING = {
    "openlabel": {
        "metadata": {"schema_version": "1.0.0"},
        "tags": {
            "0": {
                "type": "WeatherRain",
                "ontology_uid": "0",
                "tag_data": {"num": [{"val": "not_a_number"}]},
            }
        },
    }
}


# =============================================================================
# Schema Generation Tests
# =============================================================================


class TestPublishedSchema:
    """Structure of the published JSON Schema."""

    def test_schema_has_defs_and_properties(self, shipped_schema: dict) -> None:
        """The published schema is a JSON Schema with definitions."""
        assert "$defs" in shipped_schema
        assert "properties" in shipped_schema

    def test_schema_has_openlabel_root(self, shipped_schema: dict) -> None:
        """Schema should have OpenLabelFile as root with 'openlabel' property."""
        assert "openlabel" in shipped_schema["properties"]

    def test_schema_has_required_defs(self, shipped_schema: dict) -> None:
        """Schema should contain all expected definition types."""
        defs = shipped_schema["$defs"]
        expected = [
            "Attributes",
            "BooleanVal",
            "Metadata",
            "NumVal",
            "OpenLabel",
            "TagData",
            "TextVal",
            "VecVal",
        ]
        for name in expected:
            assert name in defs, f"Missing definition: {name}"

    def test_tag_type_enum_values(self, shipped_schema: dict) -> None:
        """TagEntry should constrain tag.type to enum values."""
        # Find TagEntry definition (may have __identifier_optional suffix)
        tag_defs = [k for k in shipped_schema["$defs"] if k.startswith("TagEntry")]
        assert len(tag_defs) > 0, "No TagEntry definition found"
        tag_def = shipped_schema["$defs"][tag_defs[0]]
        tag_type_prop = tag_def["properties"]["type"]

        # The enum may be inline or referenced via $ref
        if "enum" in tag_type_prop:
            enum_values = tag_type_prop["enum"]
        elif "$ref" in tag_type_prop:
            ref = tag_type_prop["$ref"]
            ref_name = ref.split("/")[-1]
            assert ref_name in shipped_schema["$defs"], (
                f"Referenced enum {ref_name} not in $defs"
            )
            enum_def = shipped_schema["$defs"][ref_name]
            enum_values = enum_def.get("enum", [])
        else:
            pytest.fail("tag.type has no enum constraint (inline or via $ref)")

        # Should contain known ontology values
        assert "WeatherRain" in enum_values
        assert "RoadTypeMinor" in enum_values
        assert "VehicleCar" in enum_values
        assert "scenarioName" in enum_values
        assert len(enum_values) >= 200

    def test_boundary_mode_enum(self, shipped_schema: dict) -> None:
        """OntologyEntry should constrain boundary_mode to enum values."""
        ont_defs = [k for k in shipped_schema["$defs"] if k.startswith("OntologyEntry")]
        assert len(ont_defs) > 0
        ont_def = shipped_schema["$defs"][ont_defs[0]]
        bm = ont_def["properties"]["boundary_mode"]

        def resolve(node: dict) -> dict:
            """Follow a local ``$ref`` into ``$defs`` (linkml emits enums by reference)."""
            ref = node.get("$ref")
            if ref and ref.startswith("#/$defs/"):
                return shipped_schema["$defs"][ref.split("/")[-1]]
            return node

        candidates = [resolve(opt) for opt in bm.get("anyOf", [])] or [resolve(bm)]
        enums = [opt["enum"] for opt in candidates if "enum" in opt]
        assert enums, f"boundary_mode has no enum constraint: {bm}"
        for values in enums:
            assert "include" in values
            assert "exclude" in values


# =============================================================================
# Schema Validation Tests (Functional Equivalence)
# =============================================================================


class TestSchemaValidation:
    """Tests that the generated schema validates ASAM v1 format files correctly."""

    def test_valid_minimal(self, shipped_schema: dict) -> None:
        """Minimal valid tagging file should pass."""
        jsonschema.validate(VALID_MINIMAL, shipped_schema)

    def test_valid_full_scenario(self, shipped_schema: dict) -> None:
        """Full scenario from spec §8.8.1 should pass."""
        jsonschema.validate(VALID_FULL_SCENARIO, shipped_schema)

    def test_valid_numeric_tag_data(self, shipped_schema: dict) -> None:
        """Numeric tag_data should pass."""
        jsonschema.validate(VALID_NUMERIC, shipped_schema)

    def test_invalid_missing_metadata(self, shipped_schema: dict) -> None:
        """Missing metadata should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_NO_METADATA, shipped_schema)

    def test_invalid_missing_tag_type(self, shipped_schema: dict) -> None:
        """Missing tag.type should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_NO_TAG_TYPE, shipped_schema)

    def test_invalid_wrong_tag_type_rejected(self, shipped_schema: dict) -> None:
        """Invalid tag.type value should be rejected (vocabulary constraint)."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_WRONG_TAG_TYPE, shipped_schema)

    def test_invalid_boundary_mode_rejected(self, shipped_schema: dict) -> None:
        """Invalid boundary_mode should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_WRONG_BOUNDARY_MODE, shipped_schema)

    def test_invalid_num_val_string_rejected(self, shipped_schema: dict) -> None:
        """String value for num.val should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_NUM_VAL_STRING, shipped_schema)


# =============================================================================
# TagTypeEnum Sync Script Tests
# =============================================================================


class TestSyncTagTypeEnum:
    """The generated tag-types.yaml is what the sync script produces today."""

    def test_check_mode_passes(self) -> None:
        """Sync script --check should pass when tag-types.yaml is up to date."""
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--check"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        assert result.returncode == 0, (
            f"tag-types.yaml is out of date. "
            f"Run: python scripts/sync_tag_type_enum.py\n{result.stdout}"
        )

    def test_schema_imports_the_generated_enum(self, shipped_schema: dict) -> None:
        """The published TagTypeEnum is the generated one, value for value."""
        generated = yaml.safe_load(TAG_TYPES_YAML.read_text(encoding="utf-8"))
        values = generated["enums"]["TagTypeEnum"]["permissible_values"]
        assert _tag_type_enum(shipped_schema) == list(values)


# =============================================================================
# Vocabulary Faithfulness (covers every ASAM tag class)
# =============================================================================


class TestVocabularyFaithfulness:
    """TagTypeEnum must accept every real ASAM v1 tag and invent none."""

    def test_enum_covers_all_asam_tag_classes(self, shipped_schema: dict) -> None:
        """Every rdfs:Class in the ASAM ontology must be a valid tag.type."""
        enum = set(_tag_type_enum(shipped_schema))
        asam_classes = _asam_tag_classes()
        missing = sorted(asam_classes - enum)
        assert not missing, f"ASAM tag classes missing from TagTypeEnum: {missing}"

    def test_enum_is_exactly_the_asam_tag_vocabulary(
        self, shipped_schema: dict
    ) -> None:
        """tag.type accepts ASAM's tag classes and administration tags, and
        nothing else: no invented value and no value property such as
        trafficAgentTypeValue, which belongs in tag_data, not in tag.type."""
        enum = _tag_type_enum(shipped_schema)
        expected = _asam_tag_classes() | _asam_admin_properties()
        assert len(enum) == len(set(enum)), "TagTypeEnum lists a value twice"
        assert set(enum) == expected, (
            f"missing={sorted(expected - set(enum))} "
            f"extra={sorted(set(enum) - expected)}"
        )

    @pytest.mark.parametrize(
        "tag",
        [
            "RoundaboutLarge",  # spec 8.2.1 headline "large roundabout"
            "SceneryJunction",
            "EnvironmentWeather",
            "BehaviourMotion",
            "OddScenery",
            "DrivableAreaSigns",  # used in spec/test boundary_list
        ],
    )
    def test_spec_hierarchy_tags_present(self, shipped_schema: dict, tag: str) -> None:
        """Mid-level hierarchy tags referenced by the spec must validate."""
        assert tag in set(_tag_type_enum(shipped_schema))


# =============================================================================
# Functional Equivalence with the ASAM schema (spec section 8 examples)
# =============================================================================


class TestFunctionalEquivalence:
    """Spec-valid ASAM v1 files must validate against BOTH ASAM and LinkML schemas."""

    # Canonical ASAM OpenLABEL v1.0.0 chapter-8 examples.
    SPEC_EXAMPLES = {
        "8.2.5_numeric_range": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://openlabel.asam.net/o.ttl"}},
                "tags": {
                    "0": {
                        "type": "LaneSpecificationDimensions",
                        "ontology_uid": "0",
                        "tag_data": {"vec": [{"type": "range", "val": [3.4, 3.7]}]},
                    }
                },
            }
        },
        "8.2.5_numeric_set": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://openlabel.asam.net/o.ttl"}},
                "tags": {
                    "0": {
                        "type": "LaneSpecificationLaneCount",
                        "ontology_uid": "0",
                        "tag_data": {"vec": [{"type": "values", "val": [2, 3]}]},
                    }
                },
            }
        },
        "8.2.4_rainfall_value": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://openlabel.asam.net/o.ttl"}},
                "tags": {
                    "0": {
                        "type": "WeatherRain",
                        "ontology_uid": "0",
                        "tag_data": {"num": [{"type": "value", "val": 3.1}]},
                    }
                },
            }
        },
        "tag_data_string": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://openlabel.asam.net/o.ttl"}},
                "tags": {
                    "0": {
                        "type": "WeatherRain",
                        "ontology_uid": "0",
                        "tag_data": "freeform",
                    }
                },
            }
        },
        "8.6_minimal": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://openlabel.asam.net/o.ttl"}},
                "tags": {"0": {"type": "SceneryJunction", "ontology_uid": "0"}},
            }
        },
        "8.2.1_ontology_entry_string": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": "https://openlabel.asam.net/o.ttl"},
                "tags": {"0": {"type": "WeatherRain", "ontology_uid": "0"}},
            }
        },
    }

    # Malformed files that BOTH schemas must reject (structural equivalence).
    SHARED_INVALID = {
        "missing_metadata": {
            "openlabel": {"tags": {"0": {"type": "WeatherRain", "ontology_uid": "0"}}}
        },
        "missing_tag_type": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "tags": {"0": {"ontology_uid": "0"}},
            }
        },
        "num_val_wrong_type": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "tags": {
                    "0": {
                        "type": "WeatherRain",
                        "ontology_uid": "0",
                        "tag_data": {"num": [{"val": "not_a_number"}]},
                    }
                },
            }
        },
    }

    # Files the ASAM schema accepts but the LinkML schema rejects (LinkML stricter).
    LINKML_STRICTER = {
        "unknown_tag_type": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "tags": {"0": {"type": "CompletelyFakeTag", "ontology_uid": "0"}},
            }
        },
        "wrong_boundary_mode": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {
                    "0": {"uri": "https://x/o", "boundary_mode": "not_a_mode"}
                },
                "tags": {"0": {"type": "WeatherRain", "ontology_uid": "0"}},
            }
        },
        # ASAM marks only tag.type required; we additionally require ontology_uid
        # (spec 8.2.1). Disclosed in SCHEMA_MODELING.md "Functional Equivalence".
        "missing_ontology_uid": {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "tags": {"0": {"type": "WeatherRain"}},
            }
        },
    }

    @pytest.mark.parametrize("name", sorted(SPEC_EXAMPLES))
    def test_spec_example_valid_in_asam(self, asam_schema: dict, name: str) -> None:
        """Sanity: each example is valid against the authoritative ASAM schema."""
        jsonschema.validate(self.SPEC_EXAMPLES[name], asam_schema)

    @pytest.mark.parametrize("name", sorted(SPEC_EXAMPLES))
    def test_spec_example_valid_in_linkml(
        self, shipped_schema: dict, name: str
    ) -> None:
        """Each ASAM-valid example must ALSO validate against the LinkML schema."""
        jsonschema.validate(self.SPEC_EXAMPLES[name], shipped_schema)

    @pytest.mark.parametrize("name", sorted(SHARED_INVALID))
    def test_shared_invalid_rejected_by_both(
        self, asam_schema: dict, shipped_schema: dict, name: str
    ) -> None:
        """Malformed files must be rejected by BOTH schemas (equivalence)."""
        data = self.SHARED_INVALID[name]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, asam_schema)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, shipped_schema)

    @pytest.mark.parametrize("name", sorted(LINKML_STRICTER))
    def test_linkml_stricter_than_asam(
        self, asam_schema: dict, shipped_schema: dict, name: str
    ) -> None:
        """Cases ASAM accepts (unconstrained) but LinkML rejects (added value)."""
        data = self.LINKML_STRICTER[name]
        jsonschema.validate(data, asam_schema)  # ASAM accepts
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, shipped_schema)


# =============================================================================
# Profile scope (tagging vs labelling)
# =============================================================================


# The exact set of OpenLABEL sections this profile accepts without validating.
# Pinned deliberately: widening it silently would enlarge the share of a file
# that can be reported valid while never having been checked.
PASSTHROUGH_SECTIONS = {
    "actions",
    "contexts",
    "coordinate_systems",
    "events",
    "frame_intervals",
    "frames",
    "objects",
    "relations",
    "streams",
}

# The sections this profile does validate.
VALIDATED_SECTIONS = {"metadata", "ontologies", "tags", "resources"}


def _refs_in(spec: dict) -> set:
    """Collect the $refs reachable from a property schema.

    Covers the shapes the generator emits for a slot: a direct ``$ref``, an
    ``items.$ref`` for a multivalued slot, and an ``anyOf`` null-wrapping. The
    published artifact still null-wraps the values of inlined dicts whose range
    has no required slot (the generator ignores ``--no-include-null`` there),
    and a consumer generating the schema without that flag gets the wrapping on
    every optional slot, so detection must accept both forms.
    """
    found = set()
    for branch in [spec, *spec.get("anyOf", []), *spec.get("oneOf", [])]:
        if not isinstance(branch, dict):
            continue
        if branch.get("$ref"):
            found.add(branch["$ref"])
        items = branch.get("items")
        if isinstance(items, dict) and items.get("$ref"):
            found.add(items["$ref"])
        # An inlined dict puts the value schema under additionalProperties,
        # itself possibly null-wrapped in an anyOf. This is the shape emitted
        # for a key-constrained passthrough section (propertyNames + value).
        addl = branch.get("additionalProperties")
        if isinstance(addl, dict):
            found |= _refs_in(addl)
    return found


# A section is passthrough when any $ref in its property schema points into the
# "Unchecked*" family: UncheckedSection (open object), or the key-constrained
# UncheckedUidEntry / UncheckedFrameEntry used where ASAM pins the dict keys.
PASSTHROUGH_MARKER = "#/$defs/Unchecked"


def _is_passthrough(subschema: dict) -> bool:
    """True when the subschema defers validation to the Unchecked* family."""
    return any(r.startswith(PASSTHROUGH_MARKER) for r in _refs_in(subschema))


def unvalidated_sections(document: dict, schema: dict) -> set:
    """Report which sections of ``document`` the schema accepts without checking.

    A section is passthrough when its property schema references a definition
    of the Unchecked family (``UncheckedSection``, ``UncheckedUidEntry``,
    ``UncheckedFrameEntry``). This is the contract an external consumer can rely
    on to tell "valid" apart from "fully checked": a ``$ref`` into
    ``#/$defs/Unchecked…`` means accepted but not validated.
    """
    props = schema["$defs"]["OpenLabel"]["properties"]
    return {
        name
        for name in document.get("openlabel", {})
        if _is_passthrough(props.get(name, {}))
    }


class TestProfileScope:
    """The profile validates tagging and passes labelling through unvalidated.

    ASAM declares ``openlabel`` with ``additionalProperties: false``, so a
    profile that omits the labelling sections rejects conformant files. Spec
    8.1.1 allows a labelling instance to be used as the raw data for tagging,
    so tags and labelling data legitimately co-occur.
    """

    def test_all_thirteen_asam_properties_declared(
        self, shipped_schema: dict, asam_schema: dict
    ) -> None:
        """Our OpenLabel must declare exactly the properties ASAM declares."""
        ours = set(shipped_schema["$defs"]["OpenLabel"]["properties"])
        theirs = set(asam_schema["definitions"]["openlabel"]["properties"])
        assert ours == theirs, f"missing={theirs - ours} extra={ours - theirs}"

    def test_container_stays_closed(self, shipped_schema: dict) -> None:
        """Enumerating the sections must not reopen the container."""
        assert shipped_schema["$defs"]["OpenLabel"]["additionalProperties"] is False

    def test_passthrough_set_is_exactly_as_pinned(self, shipped_schema: dict) -> None:
        """Widening the unvalidated surface must be a deliberate, visible change."""
        props = shipped_schema["$defs"]["OpenLabel"]["properties"]
        actual = {n for n, s in props.items() if _is_passthrough(s)}
        assert actual == PASSTHROUGH_SECTIONS
        assert set(props) == PASSTHROUGH_SECTIONS | VALIDATED_SECTIONS

    def test_validated_sections_are_not_passthrough(self, shipped_schema: dict) -> None:
        """metadata/ontologies/tags must keep their real constraints."""
        props = shipped_schema["$defs"]["OpenLabel"]["properties"]
        for name in VALIDATED_SECTIONS:
            assert not _is_passthrough(props[name]), f"{name} became passthrough"

    def test_unchecked_section_is_detectably_unconstrained(
        self, shipped_schema: dict
    ) -> None:
        """Consumers detect skipped content via this $def, so keep it unconstrained."""
        any_value = shipped_schema["$defs"]["UncheckedSection"]
        assert any_value.get("additionalProperties") is True
        assert not any_value.get("properties")
        assert not any_value.get("required")

    def test_frame_intervals_accepts_an_array(self, shipped_schema: dict) -> None:
        """linkml:Any omits "array" from its type list, so this needs multivalued."""
        doc = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "frame_intervals": [{"frame_start": 0, "frame_end": 9}],
            }
        }
        jsonschema.validate(doc, shipped_schema)

    def test_mixed_tagging_and_labelling_accepted(
        self, shipped_schema: dict, asam_schema: dict
    ) -> None:
        """Spec 8.1.1: a labelling instance may itself be tagged."""
        doc = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "tags": {"0": {"type": "WeatherRain", "ontology_uid": "0"}},
                "objects": {"0": {"name": "car1", "type": "car"}},
            }
        }
        jsonschema.validate(doc, asam_schema)
        jsonschema.validate(doc, shipped_schema)

    def test_unvalidated_sections_are_reported(self, shipped_schema: dict) -> None:
        """A caller must be able to tell "valid" from "fully checked"."""
        doc = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "tags": {"0": {"type": "WeatherRain", "ontology_uid": "0"}},
                "objects": {"0": {"name": "car1", "type": "car"}},
                "frames": {},
            }
        }
        jsonschema.validate(doc, shipped_schema)
        assert unvalidated_sections(doc, shipped_schema) == {"objects", "frames"}

    def test_pure_tagging_file_reports_nothing_skipped(
        self, shipped_schema: dict
    ) -> None:
        """The common case must not raise a false alarm."""
        assert unvalidated_sections(VALID_MINIMAL, shipped_schema) == set()

    def test_resources_entries_are_strings(
        self, shipped_schema: dict, asam_schema: dict
    ) -> None:
        """ASAM resources map a UID to a string (a file name or URL)."""
        doc = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "resources": {"0": "../scenario.xosc"},
                "tags": {
                    "0": {
                        "type": "WeatherRain",
                        "ontology_uid": "0",
                        "resource_uid": {"0": "ego"},
                    }
                },
            }
        }
        jsonschema.validate(doc, asam_schema)
        jsonschema.validate(doc, shipped_schema)
        assert unvalidated_sections(doc, shipped_schema) == set()
