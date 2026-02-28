"""Unit tests for xsd_enum_extractor module."""

import textwrap

import pytest

from src.tools.utils.xsd_enum_extractor import (
    EnumType,
    EnumValue,
    _is_deprecated,
    extract_enums_from_dir,
    extract_enums_from_file,
)


class TestIsDeprecated:
    """Tests for the _is_deprecated helper function."""

    def test_deprecated_keyword(self):
        assert _is_deprecated("deprecated") is True

    def test_deprecated_with_detail(self):
        assert _is_deprecated("deprecated, use entry instead") is True

    def test_use_instead_pattern(self):
        assert _is_deprecated("use barrier instead") is True

    def test_normal_description(self):
        assert _is_deprecated("A pole is a thin long object.") is False

    def test_none_input(self):
        assert _is_deprecated(None) is False

    def test_empty_string(self):
        assert _is_deprecated("") is False

    def test_deprecated_case_insensitive(self):
        assert _is_deprecated("Deprecated") is True

    def test_use_pattern_case_insensitive(self):
        assert _is_deprecated("Use walking instead") is True


class TestEnumValue:
    """Tests for the EnumValue dataclass."""

    def test_basic_value(self):
        v = EnumValue(value="motorway")
        assert v.value == "motorway"
        assert v.documentation is None
        assert v.deprecated is False

    def test_deprecated_value(self):
        v = EnumValue(
            value="mwyEntry",
            documentation="deprecated, use entry instead",
            deprecated=True,
        )
        assert v.deprecated is True
        assert "entry" in v.documentation


class TestEnumType:
    """Tests for the EnumType dataclass."""

    def test_value_strings_sorted(self):
        et = EnumType(
            name="test",
            values=[
                EnumValue(value="c"),
                EnumValue(value="a"),
                EnumValue(value="b"),
            ],
        )
        assert et.value_strings == ["a", "b", "c"]

    def test_non_deprecated_values(self):
        et = EnumType(
            name="test",
            values=[
                EnumValue(value="active1", deprecated=False),
                EnumValue(value="old", deprecated=True),
                EnumValue(value="active2", deprecated=False),
            ],
        )
        assert et.non_deprecated_values == ["active1", "active2"]

    def test_deprecated_values(self):
        et = EnumType(
            name="test",
            values=[
                EnumValue(value="active", deprecated=False),
                EnumValue(value="old1", deprecated=True),
                EnumValue(value="old2", deprecated=True),
            ],
        )
        assert et.deprecated_values == ["old1", "old2"]

    def test_empty_values(self):
        et = EnumType(name="empty")
        assert et.value_strings == []
        assert et.non_deprecated_values == []
        assert et.deprecated_values == []


class TestExtractEnumsFromFile:
    """Tests for extracting enums from XSD files."""

    def test_valid_xsd_file(self, tmp_path):
        xsd_content = textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                <xs:simpleType name="e_testEnum">
                    <xs:annotation>
                        <xs:documentation>A test enum</xs:documentation>
                    </xs:annotation>
                    <xs:restriction base="xs:string">
                        <xs:enumeration value="alpha">
                            <xs:annotation>
                                <xs:documentation>First value</xs:documentation>
                            </xs:annotation>
                        </xs:enumeration>
                        <xs:enumeration value="beta"/>
                        <xs:enumeration value="gamma">
                            <xs:annotation>
                                <xs:documentation>deprecated</xs:documentation>
                            </xs:annotation>
                        </xs:enumeration>
                    </xs:restriction>
                </xs:simpleType>
            </xs:schema>
        """
        )
        xsd_file = tmp_path / "test.xsd"
        xsd_file.write_text(xsd_content, encoding="utf-8")

        enums = extract_enums_from_file(xsd_file)
        assert "e_testEnum" in enums
        et = enums["e_testEnum"]
        assert et.documentation == "A test enum"
        assert et.source_file == "test.xsd"
        assert len(et.values) == 3
        assert et.value_strings == ["alpha", "beta", "gamma"]
        assert et.deprecated_values == ["gamma"]

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_enums_from_file(tmp_path / "nonexistent.xsd")

    def test_no_enums_in_file(self, tmp_path):
        xsd_content = textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                <xs:complexType name="t_something">
                    <xs:sequence>
                        <xs:element name="child" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:schema>
        """
        )
        xsd_file = tmp_path / "no_enums.xsd"
        xsd_file.write_text(xsd_content, encoding="utf-8")

        enums = extract_enums_from_file(xsd_file)
        assert len(enums) == 0

    def test_value_without_annotation(self, tmp_path):
        xsd_content = textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                <xs:simpleType name="e_simple">
                    <xs:restriction base="xs:string">
                        <xs:enumeration value="yes"/>
                        <xs:enumeration value="no"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:schema>
        """
        )
        xsd_file = tmp_path / "simple.xsd"
        xsd_file.write_text(xsd_content, encoding="utf-8")

        enums = extract_enums_from_file(xsd_file)
        assert "e_simple" in enums
        for v in enums["e_simple"].values:
            assert v.documentation is None
            assert v.deprecated is False


class TestExtractEnumsFromDir:
    """Tests for extracting enums from a directory of XSD files."""

    def test_directory_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_enums_from_dir(tmp_path / "nonexistent")

    def test_empty_directory(self, tmp_path):
        enums = extract_enums_from_dir(tmp_path)
        assert len(enums) == 0

    def test_skip_subdirs(self, tmp_path):
        # Create XSD in root
        root_xsd = tmp_path / "root.xsd"
        root_xsd.write_text(
            textwrap.dedent(
                """\
            <?xml version="1.0" encoding="UTF-8"?>
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                <xs:simpleType name="e_root">
                    <xs:restriction base="xs:string">
                        <xs:enumeration value="a"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:schema>
        """
            ),
            encoding="utf-8",
        )

        # Create XSD in subdir
        subdir = tmp_path / "local_schema"
        subdir.mkdir()
        sub_xsd = subdir / "sub.xsd"
        sub_xsd.write_text(
            textwrap.dedent(
                """\
            <?xml version="1.0" encoding="UTF-8"?>
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                <xs:simpleType name="e_sub">
                    <xs:restriction base="xs:string">
                        <xs:enumeration value="b"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:schema>
        """
            ),
            encoding="utf-8",
        )

        # skip_subdirs=True: only root
        enums = extract_enums_from_dir(tmp_path, skip_subdirs=True)
        assert "e_root" in enums
        assert "e_sub" not in enums

        # skip_subdirs=False: both
        enums = extract_enums_from_dir(tmp_path, skip_subdirs=False)
        assert "e_root" in enums
        assert "e_sub" in enums


class TestActualXsdFiles:
    """Integration tests against the actual OpenDRIVE XSD files."""

    XSD_DIR = "imports/OpenDrive/xsd_schema"

    @pytest.fixture
    def xsd_enums(self):
        from pathlib import Path

        xsd_dir = Path(self.XSD_DIR)
        if not xsd_dir.exists():
            pytest.skip("OpenDRIVE XSD files not available")
        return extract_enums_from_dir(xsd_dir)

    def test_extracts_known_enums(self, xsd_enums):
        assert "e_roadType" in xsd_enums
        assert "e_laneType" in xsd_enums
        assert "e_objectType" in xsd_enums
        assert "e_trafficRule" in xsd_enums

    def test_road_type_count(self, xsd_enums):
        assert len(xsd_enums["e_roadType"].values) == 13

    def test_lane_type_count(self, xsd_enums):
        assert len(xsd_enums["e_laneType"].values) == 31

    def test_object_type_count(self, xsd_enums):
        assert len(xsd_enums["e_objectType"].values) == 27

    def test_traffic_rule_values(self, xsd_enums):
        assert set(xsd_enums["e_trafficRule"].value_strings) == {"LHT", "RHT"}

    def test_deprecated_detection(self, xsd_enums):
        lane_types = xsd_enums["e_laneType"]
        assert "mwyEntry" in lane_types.deprecated_values
        assert "driving" in lane_types.non_deprecated_values
