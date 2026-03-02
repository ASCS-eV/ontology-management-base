#!/usr/bin/env python3
"""
XSD Enumeration Extractor - Parse XSD schemas for enum definitions.

Extracts all xs:simpleType enumerations from XSD schema files, including
their values, documentation annotations, and deprecation status. Designed
as the machine-readable bridge between XSD schemas (e.g. OpenDRIVE,
OpenSCENARIO) and SHACL sh:in constraints.

Supports two XSD enum patterns:
- Direct:  simpleType > restriction > enumeration  (OpenDRIVE style)
- Union:   simpleType > union > simpleType > restriction > enumeration
           (OpenSCENARIO style)

FEATURE SET:
============
1. extract_enums_from_file  - Extract enums from a single XSD file
2. extract_enums_from_dir   - Extract enums from all XSD files in a directory
3. EnumValue                - Dataclass for a single enum value with metadata
4. EnumType                 - Dataclass for a named enum type with its values

USAGE:
======
    from src.tools.utils.xsd_enum_extractor import extract_enums_from_dir

    # Extract all enums from an XSD directory
    enums = extract_enums_from_dir(Path("imports/OpenDrive/xsd_schema"))

    # Extract from a single XSD file
    enums = extract_enums_from_file(Path("imports/OpenScenario/OpenSCENARIO.xsd"))

    # Access specific enum
    lane_types = enums["e_laneType"]
    for val in lane_types.values:
        print(f"{val.value} (deprecated={val.deprecated}): {val.documentation}")

STANDALONE TESTING:
==================
    python3 -m src.tools.utils.xsd_enum_extractor --test

DEPENDENCIES:
=============
- xml.etree.ElementTree (stdlib): XSD parsing

NOTES:
======
- Only processes root-level XSD files (skips local_schema/ subdirectory)
- Deprecation is detected from documentation text containing 'deprecated'
- This module belongs to utils/ layer; no imports from validators/
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from src.tools.core.logging import get_logger

logger = get_logger(__name__)

XS_NS = "http://www.w3.org/2001/XMLSchema"
NS = {"xs": XS_NS}


@dataclass
class EnumValue:
    """A single enumeration value with optional documentation and deprecation status."""

    value: str
    documentation: Optional[str] = None
    deprecated: bool = False


@dataclass
class EnumType:
    """A named XSD simpleType enumeration with its values."""

    name: str
    documentation: Optional[str] = None
    source_file: Optional[str] = None
    values: list[EnumValue] = field(default_factory=list)

    @property
    def value_strings(self) -> list[str]:
        """Return just the string values, sorted alphabetically."""
        return sorted(v.value for v in self.values)

    @property
    def non_deprecated_values(self) -> list[str]:
        """Return non-deprecated values, sorted alphabetically."""
        return sorted(v.value for v in self.values if not v.deprecated)

    @property
    def deprecated_values(self) -> list[str]:
        """Return deprecated values, sorted alphabetically."""
        return sorted(v.value for v in self.values if v.deprecated)


def _is_deprecated(doc_text: Optional[str]) -> bool:
    """Check if documentation text indicates deprecation."""
    if not doc_text:
        return False
    lower = doc_text.strip().lower()
    return (
        lower.startswith("deprecated")
        or lower.startswith("use ")
        and "instead" in lower
    )


def _find_enum_elements(simple_type: ET.Element) -> list[ET.Element]:
    """Find enumeration elements in a simpleType, handling both patterns.

    Supports:
    - Direct:  simpleType > restriction > enumeration  (OpenDRIVE)
    - Union:   simpleType > union > simpleType > restriction > enumeration
               (OpenSCENARIO)
    """
    # Pattern 1: direct restriction
    restriction = simple_type.find("xs:restriction", NS)
    if restriction is not None:
        enums = restriction.findall("xs:enumeration", NS)
        if enums:
            return enums

    # Pattern 2: union wrapping an inner simpleType with restriction
    union = simple_type.find("xs:union", NS)
    if union is not None:
        for inner_st in union.findall("xs:simpleType", NS):
            inner_restriction = inner_st.find("xs:restriction", NS)
            if inner_restriction is not None:
                enums = inner_restriction.findall("xs:enumeration", NS)
                if enums:
                    return enums

    return []


def extract_enums_from_file(xsd_path: Path) -> dict[str, EnumType]:
    """Extract all xs:simpleType enumerations from a single XSD file.

    Handles both direct restriction patterns (OpenDRIVE) and union-wrapped
    restriction patterns (OpenSCENARIO).

    Args:
        xsd_path: Path to the XSD schema file.

    Returns:
        Dictionary mapping enum type names to EnumType objects.

    Raises:
        FileNotFoundError: If the XSD file does not exist.
        ET.ParseError: If the XSD file is not valid XML.
    """
    if not xsd_path.exists():
        raise FileNotFoundError(f"XSD file not found: {xsd_path}")

    tree = ET.parse(xsd_path)
    root = tree.getroot()
    enums: dict[str, EnumType] = {}

    for simple_type in root.findall("xs:simpleType", NS):
        name = simple_type.get("name", "")
        if not name:
            continue

        enum_elements = _find_enum_elements(simple_type)
        if not enum_elements:
            continue

        # Get type-level documentation
        type_doc = None
        type_annotation = simple_type.find("xs:annotation/xs:documentation", NS)
        if type_annotation is not None and type_annotation.text:
            type_doc = type_annotation.text.strip()

        enum_type = EnumType(
            name=name,
            documentation=type_doc,
            source_file=xsd_path.name,
        )

        for enum_elem in enum_elements:
            value = enum_elem.get("value", "")
            doc = None
            annotation = enum_elem.find("xs:annotation/xs:documentation", NS)
            if annotation is not None and annotation.text:
                doc = annotation.text.strip()

            enum_type.values.append(
                EnumValue(
                    value=value,
                    documentation=doc,
                    deprecated=_is_deprecated(doc),
                )
            )

        enums[name] = enum_type
        logger.debug(
            "Extracted enum '%s' with %d values from %s",
            name,
            len(enum_type.values),
            xsd_path.name,
        )

    return enums


def extract_enums_from_dir(
    xsd_dir: Path,
    skip_subdirs: bool = True,
) -> dict[str, EnumType]:
    """Extract all enumerations from XSD files in a directory.

    Args:
        xsd_dir: Path to directory containing XSD files.
        skip_subdirs: If True, only process XSD files in the root of xsd_dir
                      (skips subdirectories like local_schema/).

    Returns:
        Dictionary mapping enum type names to EnumType objects.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not xsd_dir.exists():
        raise FileNotFoundError(f"XSD directory not found: {xsd_dir}")

    if skip_subdirs:
        xsd_files = sorted(xsd_dir.glob("*.xsd"))
    else:
        xsd_files = sorted(xsd_dir.rglob("*.xsd"))

    all_enums: dict[str, EnumType] = {}

    for xsd_file in xsd_files:
        file_enums = extract_enums_from_file(xsd_file)
        all_enums.update(file_enums)

    logger.info(
        "Extracted %d enum types from %d XSD files in %s",
        len(all_enums),
        len(xsd_files),
        xsd_dir,
    )

    return all_enums


def _run_tests() -> bool:
    """Run self-tests for the module."""
    print("Running xsd_enum_extractor self-tests...")
    all_passed = True

    # Test 1: _is_deprecated detection
    try:
        assert _is_deprecated("deprecated") is True
        assert _is_deprecated("deprecated, use entry instead") is True
        assert _is_deprecated("use barrier instead") is True
        assert _is_deprecated("A pole is a thin long object.") is False
        assert _is_deprecated(None) is False
        assert _is_deprecated("") is False
        print("  PASS: _is_deprecated detection")
    except AssertionError as e:
        print(f"  FAIL: _is_deprecated detection - {e}")
        all_passed = False

    # Test 2: Extract from OpenDRIVE XSD files (direct restriction pattern)
    xsd_dir = Path("imports/OpenDrive/xsd_schema")
    if xsd_dir.exists():
        try:
            enums = extract_enums_from_dir(xsd_dir)
            assert len(enums) > 0, "Should extract at least one enum"

            # Check known enums exist
            assert "e_roadType" in enums, "e_roadType should be extracted"
            assert "e_laneType" in enums, "e_laneType should be extracted"
            assert "e_objectType" in enums, "e_objectType should be extracted"
            assert "e_trafficRule" in enums, "e_trafficRule should be extracted"

            # Check e_roadType values
            road_types = enums["e_roadType"]
            assert "motorway" in road_types.value_strings
            assert "rural" in road_types.value_strings
            assert (
                len(road_types.values) == 13
            ), f"Expected 13 road types, got {len(road_types.values)}"

            # Check e_laneType has deprecated values
            lane_types = enums["e_laneType"]
            assert (
                len(lane_types.deprecated_values) > 0
            ), "e_laneType should have deprecated values"
            assert "mwyEntry" in lane_types.deprecated_values

            # Check e_trafficRule
            traffic = enums["e_trafficRule"]
            assert set(traffic.value_strings) == {"LHT", "RHT"}

            print(f"  PASS: OpenDRIVE extraction ({len(enums)} enum types found)")
        except (AssertionError, Exception) as e:
            print(f"  FAIL: OpenDRIVE extraction - {e}")
            all_passed = False
    else:
        print("  SKIP: OpenDRIVE XSD files not found at imports/OpenDrive/xsd_schema")

    # Test 3: Extract from OpenSCENARIO XSD file (union pattern)
    xsd_file = Path("imports/OpenScenario/OpenSCENARIO.xsd")
    if xsd_file.exists():
        try:
            enums = extract_enums_from_file(xsd_file)
            assert len(enums) > 0, "Should extract at least one enum"

            # Check known enums exist
            assert "VehicleCategory" in enums, "VehicleCategory should be extracted"
            assert "ObjectType" in enums, "ObjectType should be extracted"
            assert (
                "PedestrianCategory" in enums
            ), "PedestrianCategory should be extracted"
            assert "PrecipitationType" in enums, "PrecipitationType should be extracted"
            assert (
                "MiscObjectCategory" in enums
            ), "MiscObjectCategory should be extracted"

            # Check VehicleCategory values
            vehicles = enums["VehicleCategory"]
            assert "car" in vehicles.value_strings
            assert "truck" in vehicles.value_strings
            assert "bicycle" in vehicles.value_strings
            assert (
                len(vehicles.values) == 10
            ), f"Expected 10 vehicle categories, got {len(vehicles.values)}"

            # Check PrecipitationType
            precip = enums["PrecipitationType"]
            assert set(precip.value_strings) == {"dry", "rain", "snow"}

            print(f"  PASS: OpenSCENARIO extraction ({len(enums)} enum types found)")
        except (AssertionError, Exception) as e:
            print(f"  FAIL: OpenSCENARIO extraction - {e}")
            all_passed = False
    else:
        print(
            "  SKIP: OpenSCENARIO XSD not found at imports/OpenScenario/OpenSCENARIO.xsd"
        )

    # Test 4: EnumType properties
    try:
        et = EnumType(
            name="test",
            values=[
                EnumValue(value="b", deprecated=False),
                EnumValue(value="a", deprecated=False),
                EnumValue(value="c", deprecated=True, documentation="deprecated"),
            ],
        )
        assert et.value_strings == ["a", "b", "c"]
        assert et.non_deprecated_values == ["a", "b"]
        assert et.deprecated_values == ["c"]
        print("  PASS: EnumType properties")
    except AssertionError as e:
        print(f"  FAIL: EnumType properties - {e}")
        all_passed = False

    print(f"\n{'All tests passed!' if all_passed else 'Some tests FAILED!'}")
    return all_passed


def main() -> None:
    """Entry point for standalone execution."""
    if "--test" in sys.argv:
        success = _run_tests()
        sys.exit(0 if success else 1)

    # Default: extract and display all enums from specified or default path
    xsd_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    if xsd_path is None:
        xsd_path = Path("imports/OpenDrive/xsd_schema")

    if not xsd_path.exists():
        print(f"XSD path not found: {xsd_path}")
        sys.exit(1)

    if xsd_path.is_file():
        enums = extract_enums_from_file(xsd_path)
    else:
        enums = extract_enums_from_dir(xsd_path)

    for name, enum_type in sorted(enums.items()):
        dep_count = len(enum_type.deprecated_values)
        dep_info = f" ({dep_count} deprecated)" if dep_count else ""
        print(
            f"\n{name} [{enum_type.source_file}] - {len(enum_type.values)} values{dep_info}:"
        )
        for v in enum_type.values:
            dep_marker = " [DEPRECATED]" if v.deprecated else ""
            doc = f" - {v.documentation}" if v.documentation else ""
            print(f"  {v.value}{dep_marker}{doc}")


if __name__ == "__main__":
    main()
