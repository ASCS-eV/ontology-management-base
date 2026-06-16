#!/usr/bin/env python3
"""Tests for the OpenLABEL v2 structural schema and related scripts.

Tests cover:
    1. JSON Schema generation from LinkML structural model
    2. Schema validation of spec examples (functional equivalence)
    3. TagTypeEnum sync script correctness
    4. v1→v2 converter correctness
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
SCHEMA_YAML = ROOT_DIR / "linkml" / "openlabel-v2" / "openlabel-v2-schema.yaml"
ONTOLOGY_YAML = ROOT_DIR / "linkml" / "openlabel-v2" / "openlabel-v2.yaml"
SYNC_SCRIPT = ROOT_DIR / "scripts" / "sync_tag_type_enum.py"
CONVERT_SCRIPT = ROOT_DIR / "scripts" / "convert_openlabel_v1_to_v2.py"
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


def _asam_tag_classes() -> set[str]:
    """Local names of every rdfs:Class in the ASAM scenario tagging ontology."""
    ttl = ASAM_ONTOLOGY_TTL.read_text(encoding="utf-8")
    return set(re.findall(r"<([A-Za-z]\w*)>\s+a\s+rdfs:Class", ttl))


def _tag_type_enum(schema: dict) -> list[str]:
    """Extract the TagTypeEnum permissible values from a generated JSON Schema."""
    return schema["$defs"]["TagTypeEnum"]["enum"]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def generated_schema() -> dict:
    """Generate JSON Schema from the structural LinkML model."""
    result = subprocess.run(
        [sys.executable, "-m", "linkml.generators.jsonschemagen", str(SCHEMA_YAML)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
    )
    assert result.returncode == 0, f"gen-json-schema failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def asam_schema() -> dict:
    """Load the authoritative ASAM OpenLABEL v1.0.0 JSON Schema."""
    return json.loads(ASAM_SCHEMA.read_text(encoding="utf-8"))


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


class TestSchemaGeneration:
    """Tests for JSON Schema generation from LinkML model."""

    def test_schema_generates_successfully(self, generated_schema: dict) -> None:
        """JSON Schema generation should succeed."""
        assert "$defs" in generated_schema
        assert "properties" in generated_schema

    def test_schema_has_openlabel_root(self, generated_schema: dict) -> None:
        """Schema should have OpenLabelFile as root with 'openlabel' property."""
        assert "openlabel" in generated_schema["properties"]

    def test_schema_has_required_defs(self, generated_schema: dict) -> None:
        """Schema should contain all expected definition types."""
        defs = generated_schema["$defs"]
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

    def test_tag_type_enum_values(self, generated_schema: dict) -> None:
        """TagEntry should constrain tag.type to enum values."""
        # Find TagEntry definition (may have __identifier_optional suffix)
        tag_defs = [k for k in generated_schema["$defs"] if k.startswith("TagEntry")]
        assert len(tag_defs) > 0, "No TagEntry definition found"
        tag_def = generated_schema["$defs"][tag_defs[0]]
        tag_type_prop = tag_def["properties"]["type"]

        # The enum may be inline or referenced via $ref
        if "enum" in tag_type_prop:
            enum_values = tag_type_prop["enum"]
        elif "$ref" in tag_type_prop:
            ref = tag_type_prop["$ref"]
            ref_name = ref.split("/")[-1]
            assert ref_name in generated_schema["$defs"], (
                f"Referenced enum {ref_name} not in $defs"
            )
            enum_def = generated_schema["$defs"][ref_name]
            enum_values = enum_def.get("enum", [])
        else:
            pytest.fail("tag.type has no enum constraint (inline or via $ref)")

        # Should contain known ontology values
        assert "WeatherRain" in enum_values
        assert "RoadTypeMinor" in enum_values
        assert "VehicleCar" in enum_values
        assert "scenarioName" in enum_values
        assert len(enum_values) >= 200

    def test_boundary_mode_enum(self, generated_schema: dict) -> None:
        """OntologyEntry should constrain boundary_mode to enum values."""
        ont_defs = [
            k for k in generated_schema["$defs"] if k.startswith("OntologyEntry")
        ]
        assert len(ont_defs) > 0
        ont_def = generated_schema["$defs"][ont_defs[0]]
        bm = ont_def["properties"]["boundary_mode"]
        # Should have enum constraint (may be in anyOf or directly)
        if "enum" in bm:
            assert "include" in bm["enum"]
            assert "exclude" in bm["enum"]
        elif "anyOf" in bm:
            enum_found = False
            for opt in bm["anyOf"]:
                if "enum" in opt:
                    assert "include" in opt["enum"]
                    enum_found = True
            assert enum_found


# =============================================================================
# Schema Validation Tests (Functional Equivalence)
# =============================================================================


class TestSchemaValidation:
    """Tests that the generated schema validates ASAM v1 format files correctly."""

    def test_valid_minimal(self, generated_schema: dict) -> None:
        """Minimal valid tagging file should pass."""
        jsonschema.validate(VALID_MINIMAL, generated_schema)

    def test_valid_full_scenario(self, generated_schema: dict) -> None:
        """Full scenario from spec §8.8.1 should pass."""
        jsonschema.validate(VALID_FULL_SCENARIO, generated_schema)

    def test_valid_numeric_tag_data(self, generated_schema: dict) -> None:
        """Numeric tag_data should pass."""
        jsonschema.validate(VALID_NUMERIC, generated_schema)

    def test_invalid_missing_metadata(self, generated_schema: dict) -> None:
        """Missing metadata should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_NO_METADATA, generated_schema)

    def test_invalid_missing_tag_type(self, generated_schema: dict) -> None:
        """Missing tag.type should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_NO_TAG_TYPE, generated_schema)

    def test_invalid_wrong_tag_type_rejected(self, generated_schema: dict) -> None:
        """Invalid tag.type value should be rejected (vocabulary constraint)."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_WRONG_TAG_TYPE, generated_schema)

    def test_invalid_boundary_mode_rejected(self, generated_schema: dict) -> None:
        """Invalid boundary_mode should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_WRONG_BOUNDARY_MODE, generated_schema)

    def test_invalid_num_val_string_rejected(self, generated_schema: dict) -> None:
        """String value for num.val should be rejected."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_NUM_VAL_STRING, generated_schema)


# =============================================================================
# TagTypeEnum Sync Script Tests
# =============================================================================


class TestSyncTagTypeEnum:
    """Tests for the TagTypeEnum synchronization script."""

    @pytest.mark.skipif(not SYNC_SCRIPT.exists(), reason="sync script not found")
    def test_check_mode_passes(self) -> None:
        """Sync script --check should pass when enum is up to date."""
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--check"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        assert result.returncode == 0, (
            f"TagTypeEnum is out of sync. "
            f"Run: python scripts/sync_tag_type_enum.py\n{result.stdout}"
        )

    @pytest.mark.skipif(not SYNC_SCRIPT.exists(), reason="sync script not found")
    def test_enum_count_floor(self) -> None:
        """TagTypeEnum should expose the full ASAM vocabulary (>= 256 values)."""
        import yaml

        with open(SCHEMA_YAML) as f:
            schema = yaml.safe_load(f)
        actual_count = len(schema["enums"]["TagTypeEnum"]["permissible_values"])
        assert actual_count >= 256, (
            f"TagTypeEnum has {actual_count} values, expected >= 256 "
            f"(full ASAM tag-class + admin + enum vocabulary)"
        )


# =============================================================================
# Vocabulary Faithfulness (covers every ASAM tag class)
# =============================================================================


class TestVocabularyFaithfulness:
    """TagTypeEnum must accept every real ASAM v1 tag and invent none."""

    def test_enum_covers_all_asam_tag_classes(self, generated_schema: dict) -> None:
        """Every rdfs:Class in the ASAM ontology must be a valid tag.type."""
        enum = set(_tag_type_enum(generated_schema))
        asam_classes = _asam_tag_classes()
        missing = sorted(asam_classes - enum)
        assert not missing, f"ASAM tag classes missing from TagTypeEnum: {missing}"

    def test_no_fabricated_enum_values(self, generated_schema: dict) -> None:
        """Every enum value must be a real ASAM ontology name (class or property)."""
        ttl = ASAM_ONTOLOGY_TTL.read_text(encoding="utf-8")
        asam_names = set(
            re.findall(r"<([A-Za-z]\w*)>\s+a\s+rdfs:(?:Class|Property)", ttl)
        )
        enum = set(_tag_type_enum(generated_schema))
        fabricated = sorted(enum - asam_names)
        assert not fabricated, f"TagTypeEnum has non-ASAM values: {fabricated}"

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
    def test_spec_hierarchy_tags_present(
        self, generated_schema: dict, tag: str
    ) -> None:
        """Mid-level hierarchy tags referenced by the spec must validate."""
        assert tag in set(_tag_type_enum(generated_schema))


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
    }

    @pytest.mark.parametrize("name", sorted(SPEC_EXAMPLES))
    def test_spec_example_valid_in_asam(self, asam_schema: dict, name: str) -> None:
        """Sanity: each example is valid against the authoritative ASAM schema."""
        jsonschema.validate(self.SPEC_EXAMPLES[name], asam_schema)

    @pytest.mark.parametrize("name", sorted(SPEC_EXAMPLES))
    def test_spec_example_valid_in_linkml(
        self, generated_schema: dict, name: str
    ) -> None:
        """Each ASAM-valid example must ALSO validate against the LinkML schema."""
        jsonschema.validate(self.SPEC_EXAMPLES[name], generated_schema)

    @pytest.mark.parametrize("name", sorted(SHARED_INVALID))
    def test_shared_invalid_rejected_by_both(
        self, asam_schema: dict, generated_schema: dict, name: str
    ) -> None:
        """Malformed files must be rejected by BOTH schemas (equivalence)."""
        data = self.SHARED_INVALID[name]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, asam_schema)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, generated_schema)

    @pytest.mark.parametrize("name", sorted(LINKML_STRICTER))
    def test_linkml_stricter_than_asam(
        self, asam_schema: dict, generated_schema: dict, name: str
    ) -> None:
        """Cases ASAM accepts (unconstrained) but LinkML rejects (added value)."""
        data = self.LINKML_STRICTER[name]
        jsonschema.validate(data, asam_schema)  # ASAM accepts
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, generated_schema)


# =============================================================================
# v1→v2 Converter Tests
# =============================================================================


class TestV1ToV2Converter:
    """Tests for the ASAM v1→v2 format converter."""

    @pytest.mark.skipif(
        not CONVERT_SCRIPT.exists(), reason="converter script not found"
    )
    def test_converter_produces_valid_jsonld(self, tmp_path: Path) -> None:
        """Converter output should be valid JSON with @context."""
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(VALID_MINIMAL))

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT), str(input_file)],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        assert result.returncode == 0, f"Converter failed: {result.stderr}"
        output = json.loads(result.stdout)
        assert "@context" in output
        assert "@type" in output
        assert output["@type"] == "Tag"

    @pytest.mark.skipif(
        not CONVERT_SCRIPT.exists(), reason="converter script not found"
    )
    def test_converter_maps_boolean_flags(self, tmp_path: Path) -> None:
        """Boolean tag types should map to True values in v2."""
        v1_data = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://example.org/ont"}},
                "tags": {
                    "0": {"type": "WeatherRain", "ontology_uid": "0"},
                    "1": {"type": "MotionDrive", "ontology_uid": "0"},
                },
            }
        }
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(v1_data))

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT), str(input_file)],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        output = json.loads(result.stdout)
        assert output.get("Odd", {}).get("WeatherRain") is True
        assert output.get("Behaviour", {}).get("MotionDrive") is True

    @pytest.mark.skipif(
        not CONVERT_SCRIPT.exists(), reason="converter script not found"
    )
    def test_converter_maps_enum_values(self, tmp_path: Path) -> None:
        """Enum tag values should map to their slot with value."""
        v1_data = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://example.org/ont"}},
                "tags": {
                    "0": {"type": "RoadTypeMinor", "ontology_uid": "0"},
                    "1": {"type": "VehicleCar", "ontology_uid": "0"},
                },
            }
        }
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(v1_data))

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT), str(input_file)],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        output = json.loads(result.stdout)
        assert output.get("Odd", {}).get("DrivableAreaType") == "RoadTypeMinor"
        assert output.get("RoadUser", {}).get("RoadUserVehicle") == "VehicleCar"

    @pytest.mark.skipif(
        not CONVERT_SCRIPT.exists(), reason="converter script not found"
    )
    def test_converter_maps_admin_tags(self, tmp_path: Path) -> None:
        """Admin tags with text values should map correctly."""
        v1_data = {
            "openlabel": {
                "metadata": {"schema_version": "1.0.0"},
                "ontologies": {"0": {"uri": "https://example.org/ont"}},
                "tags": {
                    "0": {
                        "type": "scenarioName",
                        "ontology_uid": "0",
                        "tag_data": {"text": [{"type": "value", "val": "My Scenario"}]},
                    }
                },
            }
        }
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(v1_data))

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT), str(input_file)],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        output = json.loads(result.stdout)
        assert output.get("AdminTag", {}).get("scenarioName") == "My Scenario"
