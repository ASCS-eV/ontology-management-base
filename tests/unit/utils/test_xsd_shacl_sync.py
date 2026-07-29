"""Unit tests for xsd_shacl_sync module."""

import textwrap
from pathlib import Path

import pytest

from omb.core.constants import ASAM_OPENDRIVE_SCHEMA_DIR
from omb.utils.xsd_enum_extractor import EnumType, EnumValue
from omb.utils.xsd_shacl_sync import (
    EnumComparisonResult,
    SyncReport,
    compare_enums,
    extract_shacl_enums,
    run_sync_check,
)


class TestEnumComparisonResult:
    """Tests for EnumComparisonResult dataclass."""

    def test_in_sync(self):
        r = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="testProp",
            description="Test",
            xsd_values={"a", "b", "c"},
            shacl_values={"a", "b", "c"},
        )
        assert r.in_sync is True

    def test_missing_values(self):
        r = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="testProp",
            description="Test",
            xsd_values={"a", "b", "c"},
            shacl_values={"a"},
            missing_in_shacl={"b", "c"},
        )
        assert r.in_sync is False
        assert "2 missing" in r.summary()

    def test_extra_values(self):
        r = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="testProp",
            description="Test",
            xsd_values={"a"},
            shacl_values={"a", "d"},
            extra_in_shacl={"d"},
        )
        assert r.in_sync is False
        assert "1 undeclared extra" in r.summary()

    def test_declared_extension_is_not_drift(self):
        """A value declared as an ecosystem extension is in sync, and is named."""
        r = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="testProp",
            description="Test",
            xsd_values={"a"},
            shacl_values={"a", "truck"},
            extra_in_shacl={"truck"},
            declared_extensions={"truck"},
        )
        assert r.undeclared_extras == set()
        assert r.in_sync is True
        assert "declared extension: truck" in r.summary()

    def test_summary_icons(self):
        synced = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="p",
            description="Test",
            xsd_values={"a"},
            shacl_values={"a"},
        )
        assert "✅" in synced.summary()

        drifted = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="p",
            description="Test",
            xsd_values={"a", "b"},
            shacl_values={"a"},
            missing_in_shacl={"b"},
        )
        assert "❌" in drifted.summary()


class TestSyncReport:
    """Tests for SyncReport dataclass."""

    def test_all_in_sync(self):
        report = SyncReport(
            results=[
                EnumComparisonResult(
                    xsd_enum_name="e1",
                    shacl_property="p1",
                    description="D1",
                    xsd_values={"a"},
                    shacl_values={"a"},
                ),
                EnumComparisonResult(
                    xsd_enum_name="e2",
                    shacl_property="p2",
                    description="D2",
                    xsd_values={"b"},
                    shacl_values={"b"},
                ),
            ]
        )
        assert report.all_in_sync is True

    def test_not_all_in_sync(self):
        report = SyncReport(
            results=[
                EnumComparisonResult(
                    xsd_enum_name="e1",
                    shacl_property="p1",
                    description="D1",
                    xsd_values={"a"},
                    shacl_values={"a"},
                ),
                EnumComparisonResult(
                    xsd_enum_name="e2",
                    shacl_property="p2",
                    description="D2",
                    xsd_values={"b", "c"},
                    shacl_values={"b"},
                    missing_in_shacl={"c"},
                ),
            ]
        )
        assert report.all_in_sync is False

    def test_empty_report(self):
        report = SyncReport()
        assert report.all_in_sync is True


class TestCompareEnums:
    """Tests for the compare_enums function."""

    def test_matching_enums(self):
        xsd_enums = {
            "e_test": EnumType(
                name="e_test",
                values=[
                    EnumValue(value="a"),
                    EnumValue(value="b"),
                ],
            ),
        }
        shacl_enums = {"testProp": {"a", "b"}}
        mappings = [
            {
                "xsd_enum": "e_test",
                "shacl_property": "testProp",
                "shacl_prefix": "http://example.org/",
                "description": "Test mapping",
            }
        ]

        results = compare_enums(xsd_enums, shacl_enums, mappings)
        assert len(results) == 1
        assert results[0].in_sync is True

    def test_missing_xsd_enum(self):
        xsd_enums = {}
        shacl_enums = {"testProp": {"a"}}
        mappings = [
            {
                "xsd_enum": "e_nonexistent",
                "shacl_property": "testProp",
                "shacl_prefix": "http://example.org/",
                "description": "Missing mapping",
            }
        ]

        results = compare_enums(xsd_enums, shacl_enums, mappings)
        assert len(results) == 0  # Skipped due to missing XSD enum

    def test_deprecated_tracking(self):
        xsd_enums = {
            "e_test": EnumType(
                name="e_test",
                values=[
                    EnumValue(value="active"),
                    EnumValue(value="old", deprecated=True),
                ],
            ),
        }
        shacl_enums = {"testProp": {"active", "old"}}
        mappings = [
            {
                "xsd_enum": "e_test",
                "shacl_property": "testProp",
                "shacl_prefix": "http://example.org/",
                "description": "Deprecated test",
            }
        ]

        results = compare_enums(xsd_enums, shacl_enums, mappings)
        assert len(results) == 1
        assert results[0].in_sync is True
        assert "old" in results[0].deprecated_in_xsd


class TestExtractShaclEnums:
    """Tests for extracting sh:in values from SHACL Turtle files."""

    def test_extract_from_turtle(self, tmp_path):
        ttl_content = textwrap.dedent(
            """\
            @prefix sh: <http://www.w3.org/ns/shacl#> .
            @prefix ex: <http://example.org/> .

            ex:TestShape a sh:NodeShape ;
                sh:property [
                    sh:path ex:testProp ;
                    sh:in ("alpha" "beta" "gamma") ;
                ] .
        """
        )
        ttl_file = tmp_path / "test.shacl.ttl"
        ttl_file.write_text(ttl_content, encoding="utf-8")

        mappings = [
            {
                "xsd_enum": "e_test",
                "shacl_property": "testProp",
                "shacl_prefix": "http://example.org/",
                "description": "Test",
            }
        ]

        result = extract_shacl_enums(ttl_file, mappings)
        assert "testProp" in result
        assert result["testProp"] == {"alpha", "beta", "gamma"}

    def test_no_matching_property(self, tmp_path):
        ttl_content = textwrap.dedent(
            """\
            @prefix sh: <http://www.w3.org/ns/shacl#> .
            @prefix ex: <http://example.org/> .

            ex:TestShape a sh:NodeShape ;
                sh:property [
                    sh:path ex:otherProp ;
                    sh:in ("x" "y") ;
                ] .
        """
        )
        ttl_file = tmp_path / "test.shacl.ttl"
        ttl_file.write_text(ttl_content, encoding="utf-8")

        mappings = [
            {
                "xsd_enum": "e_test",
                "shacl_property": "testProp",
                "shacl_prefix": "http://example.org/",
                "description": "Test",
            }
        ]

        result = extract_shacl_enums(ttl_file, mappings)
        assert "testProp" not in result


class TestActualSyncCheck:
    """Integration tests against the actual hdmap files."""

    XSD_DIR = Path(ASAM_OPENDRIVE_SCHEMA_DIR)
    SHACL_PATH = Path("artifacts/hdmap/hdmap.shacl.ttl")

    @pytest.fixture
    def sync_report(self):
        if not self.XSD_DIR.exists() or not self.SHACL_PATH.exists():
            pytest.skip("XSD or SHACL files not available")
        return run_sync_check(self.XSD_DIR, self.SHACL_PATH)

    def test_all_mappings_checked(self, sync_report):
        assert len(sync_report.results) == 3

    # hdmap constrains all three properties through version-conditional sh:or branches
    # on DomainSpecificationShape, addressed by sequence paths
    # (sh:path ( hdmap:hasContent hdmap:laneTypes )). extract_shacl_enums used to match
    # direct paths only, so it reported every value missing and these tests asserted that
    # emptiness as expected behaviour - freezing the defect in place. It reads both forms
    # now, so they assert the real contract: the pinned enumeration is fully expressible.
    # See: https://github.com/ASCS-eV/ontology-management-base/issues/48

    def test_all_in_sync(self, sync_report):
        """Every mapped enum matches its pinned XSD, declared extensions aside."""
        assert sync_report.all_in_sync, "\n".join(
            r.summary() for r in sync_report.results
        )

    def test_road_types(self, sync_report):
        road = next(r for r in sync_report.results if r.shacl_property == "roadTypes")
        assert len(road.xsd_values) == 13  # V1.9.0 e_roadType
        assert road.shacl_values == road.xsd_values

    def test_lane_types(self, sync_report):
        lane = next(r for r in sync_report.results if r.shacl_property == "laneTypes")
        assert len(lane.xsd_values) == 31  # V1.9.0 e_laneType
        assert lane.shacl_values == lane.xsd_values
        # Deprecated values stay accepted so existing assets keep validating.
        assert lane.deprecated_in_xsd <= lane.shacl_values

    def test_level_of_detail(self, sync_report):
        lod = next(
            r for r in sync_report.results if r.shacl_property == "levelOfDetail"
        )
        assert len(lod.xsd_values) == 27  # V1.9.0 e_objectType
        # "truck" is an ENVITED-X extension, declared in the mapping, not ASAM drift.
        assert lod.extra_in_shacl == {"truck"}
        assert lod.undeclared_extras == set()
        assert lod.missing_in_shacl == set()
        assert lod.in_sync

    def test_unmapped_enums_reported(self, sync_report):
        assert len(sync_report.unmapped_xsd_enums) > 0
        assert "e_trafficRule" in sync_report.unmapped_xsd_enums
