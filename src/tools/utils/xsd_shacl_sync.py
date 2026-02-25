#!/usr/bin/env python3
"""
XSD-SHACL Sync Checker - Compare OpenDRIVE XSD enums against hdmap SHACL shapes.

Validates that the sh:in enum lists in hdmap.shacl.ttl stay synchronised
with the authoritative OpenDRIVE XSD schema definitions. Reports missing,
extra, and deprecated values.

FEATURE SET:
============
1. ShaclEnumMapping      - Configurable mapping: XSD enum type -> SHACL property
2. extract_shacl_enums   - Parse sh:in lists from a Turtle SHACL file
3. compare_enums         - Compare XSD-extracted values against SHACL values
4. run_sync_check        - Full pipeline: load XSD + SHACL, compare, report

USAGE:
======
    from src.tools.utils.xsd_shacl_sync import run_sync_check
    from pathlib import Path

    # Run full sync check
    report = run_sync_check(
        xsd_dir=Path("imports/OpenDrive/xsd_schema"),
        shacl_path=Path("artifacts/hdmap/hdmap.shacl.ttl"),
    )
    report.print_report()

STANDALONE TESTING:
==================
    python3 -m src.tools.utils.xsd_shacl_sync --test
    python3 -m src.tools.utils.xsd_shacl_sync --check  # Run actual sync check

DEPENDENCIES:
=============
- rdflib: Turtle/RDF parsing for SHACL files
- xml.etree.ElementTree (stdlib): via xsd_enum_extractor

NOTES:
======
- The mapping config defines which XSD enum maps to which SHACL sh:path
- hdmap:trafficDirection uses different values than e_trafficRule (semantic mapping)
- hdmap:formatType is hdmap-specific (not from OpenDRIVE) and is excluded
- This module belongs to utils/ layer; no imports from validators/
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

from rdflib import Graph, Namespace
from rdflib.term import Literal

from src.tools.core.logging import get_logger
from src.tools.utils.xsd_enum_extractor import EnumType, extract_enums_from_dir

logger = get_logger(__name__)

SH = Namespace("http://www.w3.org/ns/shacl#")

# Default mapping: XSD enum type name -> (SHACL namespace, property local name)
# Only enums that have a direct 1:1 value mapping are included.
HDMAP_ENUM_MAPPINGS: list[dict[str, str]] = [
    {
        "xsd_enum": "e_roadType",
        "shacl_property": "roadTypes",
        "shacl_prefix": "https://w3id.org/ascs-ev/envited-x/hdmap/v5/",
        "description": "Road types (OpenDRIVE -> hdmap:roadTypes)",
    },
    {
        "xsd_enum": "e_laneType",
        "shacl_property": "laneTypes",
        "shacl_prefix": "https://w3id.org/ascs-ev/envited-x/hdmap/v5/",
        "description": "Lane types (OpenDRIVE -> hdmap:laneTypes)",
    },
    {
        "xsd_enum": "e_objectType",
        "shacl_property": "levelOfDetail",
        "shacl_prefix": "https://w3id.org/ascs-ev/envited-x/hdmap/v5/",
        "description": "Object types / level of detail (OpenDRIVE -> hdmap:levelOfDetail)",
    },
]


@dataclass
class EnumComparisonResult:
    """Result of comparing XSD enum values against SHACL sh:in values."""

    xsd_enum_name: str
    shacl_property: str
    description: str
    xsd_values: set[str]
    shacl_values: set[str]
    missing_in_shacl: set[str] = field(default_factory=set)
    extra_in_shacl: set[str] = field(default_factory=set)
    deprecated_in_xsd: set[str] = field(default_factory=set)

    @property
    def in_sync(self) -> bool:
        """True if SHACL and XSD values match exactly."""
        return len(self.missing_in_shacl) == 0 and len(self.extra_in_shacl) == 0

    def summary(self) -> str:
        """One-line summary of the comparison."""
        if self.in_sync:
            return f"✅ {self.description}: {len(self.shacl_values)} values in sync"
        parts = []
        if self.missing_in_shacl:
            parts.append(f"{len(self.missing_in_shacl)} missing in SHACL")
        if self.extra_in_shacl:
            parts.append(f"{len(self.extra_in_shacl)} extra in SHACL")
        return f"❌ {self.description}: {', '.join(parts)}"


@dataclass
class SyncReport:
    """Full sync report across all mapped enums."""

    results: list[EnumComparisonResult] = field(default_factory=list)
    unmapped_xsd_enums: list[str] = field(default_factory=list)

    @property
    def all_in_sync(self) -> bool:
        """True if all mapped enums are in sync."""
        return all(r.in_sync for r in self.results)

    def print_report(self) -> None:
        """Print a human-readable sync report."""
        print("\n" + "=" * 70)
        print("XSD-SHACL Enum Sync Report")
        print("=" * 70)

        for result in self.results:
            print(f"\n{result.summary()}")
            if not result.in_sync:
                if result.missing_in_shacl:
                    print(f"  Missing in SHACL: {sorted(result.missing_in_shacl)}")
                if result.extra_in_shacl:
                    print(f"  Extra in SHACL:   {sorted(result.extra_in_shacl)}")
            if result.deprecated_in_xsd:
                dep_in_shacl = result.deprecated_in_xsd & result.shacl_values
                if dep_in_shacl:
                    print(f"  Deprecated (included in SHACL): {sorted(dep_in_shacl)}")

        status = "✅ ALL IN SYNC" if self.all_in_sync else "⚠️  DRIFT DETECTED"
        print(f"\n{'=' * 70}")
        print(f"Status: {status}")
        print(f"{'=' * 70}\n")


def extract_shacl_enums(
    shacl_path: Path,
    mappings: list[dict[str, str]] | None = None,
) -> dict[str, set[str]]:
    """Extract sh:in enum values from a SHACL Turtle file.

    Args:
        shacl_path: Path to the .shacl.ttl file.
        mappings: List of mapping dicts with 'shacl_property' and 'shacl_prefix'.

    Returns:
        Dictionary mapping property local names to sets of string values.
    """
    if mappings is None:
        mappings = HDMAP_ENUM_MAPPINGS

    g = Graph()
    g.parse(shacl_path, format="turtle")

    result: dict[str, set[str]] = {}

    for mapping in mappings:
        prop_name = mapping["shacl_property"]
        prop_uri = mapping["shacl_prefix"] + prop_name

        # Find property shapes that use this sh:path
        query = (
            """
        SELECT ?listItem WHERE {
            ?shape sh:property ?propShape .
            ?propShape sh:path <%s> .
            ?propShape sh:in ?list .
            ?list rdf:rest*/rdf:first ?listItem .
        }
        """
            % prop_uri
        )

        values = set()
        for row in g.query(query):
            item = row[0]
            if isinstance(item, Literal):
                values.add(str(item))

        if values:
            result[prop_name] = values
            logger.debug("Extracted %d SHACL values for %s", len(values), prop_name)
        else:
            logger.warning("No sh:in values found for %s in %s", prop_name, shacl_path)

    return result


def compare_enums(
    xsd_enums: dict[str, EnumType],
    shacl_enums: dict[str, set[str]],
    mappings: list[dict[str, str]] | None = None,
) -> list[EnumComparisonResult]:
    """Compare XSD enum values against SHACL sh:in values.

    Args:
        xsd_enums: Dictionary of XSD enum types (from extract_enums_from_dir).
        shacl_enums: Dictionary of SHACL property values (from extract_shacl_enums).
        mappings: Mapping configuration.

    Returns:
        List of comparison results.
    """
    if mappings is None:
        mappings = HDMAP_ENUM_MAPPINGS

    results = []

    for mapping in mappings:
        xsd_name = mapping["xsd_enum"]
        shacl_prop = mapping["shacl_property"]
        description = mapping["description"]

        xsd_type = xsd_enums.get(xsd_name)
        shacl_vals = shacl_enums.get(shacl_prop, set())

        if xsd_type is None:
            logger.warning("XSD enum '%s' not found", xsd_name)
            continue

        xsd_vals = set(xsd_type.value_strings)
        deprecated = set(xsd_type.deprecated_values)

        result = EnumComparisonResult(
            xsd_enum_name=xsd_name,
            shacl_property=shacl_prop,
            description=description,
            xsd_values=xsd_vals,
            shacl_values=shacl_vals,
            missing_in_shacl=xsd_vals - shacl_vals,
            extra_in_shacl=shacl_vals - xsd_vals,
            deprecated_in_xsd=deprecated,
        )
        results.append(result)

    return results


def run_sync_check(
    xsd_dir: Path,
    shacl_path: Path,
    mappings: list[dict[str, str]] | None = None,
) -> SyncReport:
    """Run a full XSD-to-SHACL enum sync check.

    Args:
        xsd_dir: Path to directory containing OpenDRIVE XSD files.
        shacl_path: Path to hdmap.shacl.ttl file.
        mappings: Optional custom mapping configuration.

    Returns:
        SyncReport with comparison results.
    """
    if mappings is None:
        mappings = HDMAP_ENUM_MAPPINGS

    logger.info("Running XSD-SHACL sync check...")
    logger.info("  XSD dir:  %s", xsd_dir)
    logger.info("  SHACL:    %s", shacl_path)

    xsd_enums = extract_enums_from_dir(xsd_dir)
    shacl_enums = extract_shacl_enums(shacl_path, mappings)
    results = compare_enums(xsd_enums, shacl_enums, mappings)

    # Find unmapped XSD enums for informational purposes
    mapped_names = {m["xsd_enum"] for m in mappings}
    unmapped = sorted(set(xsd_enums.keys()) - mapped_names)

    report = SyncReport(results=results, unmapped_xsd_enums=unmapped)
    return report


def _run_tests() -> bool:
    """Run self-tests for the module."""
    print("Running xsd_shacl_sync self-tests...")
    all_passed = True

    # Test 1: EnumComparisonResult
    try:
        r = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="testProp",
            description="Test enum",
            xsd_values={"a", "b", "c"},
            shacl_values={"a", "b", "c"},
        )
        assert r.in_sync is True
        assert "✅" in r.summary()
        print("  PASS: EnumComparisonResult (in sync)")
    except AssertionError as e:
        print(f"  FAIL: EnumComparisonResult (in sync) - {e}")
        all_passed = False

    # Test 2: EnumComparisonResult with drift
    try:
        r = EnumComparisonResult(
            xsd_enum_name="e_test",
            shacl_property="testProp",
            description="Test enum",
            xsd_values={"a", "b", "c"},
            shacl_values={"a", "d"},
            missing_in_shacl={"b", "c"},
            extra_in_shacl={"d"},
        )
        assert r.in_sync is False
        assert "❌" in r.summary()
        assert "2 missing" in r.summary()
        assert "1 extra" in r.summary()
        print("  PASS: EnumComparisonResult (drift)")
    except AssertionError as e:
        print(f"  FAIL: EnumComparisonResult (drift) - {e}")
        all_passed = False

    # Test 3: Full sync check against actual files
    xsd_dir = Path("imports/OpenDrive/xsd_schema")
    shacl_path = Path("artifacts/hdmap/hdmap.shacl.ttl")
    if xsd_dir.exists() and shacl_path.exists():
        try:
            report = run_sync_check(xsd_dir, shacl_path)
            assert (
                len(report.results) == 3
            ), f"Expected 3 results, got {len(report.results)}"
            for result in report.results:
                assert (
                    len(result.shacl_values) > 0
                ), f"No SHACL values for {result.shacl_property}"
                assert (
                    len(result.xsd_values) > 0
                ), f"No XSD values for {result.xsd_enum_name}"
            print(f"  PASS: Full sync check ({len(report.results)} mappings checked)")

            # Report sync status
            for result in report.results:
                status = "in sync" if result.in_sync else "DRIFT"
                print(f"    {result.shacl_property}: {status}")
        except (AssertionError, Exception) as e:
            print(f"  FAIL: Full sync check - {e}")
            all_passed = False
    else:
        print("  SKIP: XSD or SHACL files not found")

    print(f"\n{'All tests passed!' if all_passed else 'Some tests FAILED!'}")
    return all_passed


def main() -> None:
    """Entry point for standalone execution."""
    if "--test" in sys.argv:
        success = _run_tests()
        sys.exit(0 if success else 1)

    if "--check" in sys.argv:
        xsd_dir = Path("imports/OpenDrive/xsd_schema")
        shacl_path = Path("artifacts/hdmap/hdmap.shacl.ttl")

        if not xsd_dir.exists():
            print(f"XSD directory not found: {xsd_dir}")
            sys.exit(1)
        if not shacl_path.exists():
            print(f"SHACL file not found: {shacl_path}")
            sys.exit(1)

        report = run_sync_check(xsd_dir, shacl_path)
        report.print_report()

        if report.unmapped_xsd_enums:
            print(f"Unmapped XSD enums ({len(report.unmapped_xsd_enums)}):")
            for name in report.unmapped_xsd_enums:
                print(f"  {name}")

        sys.exit(0 if report.all_in_sync else 1)

    print("Usage: python3 -m src.tools.utils.xsd_shacl_sync [--test | --check]")
    sys.exit(1)


if __name__ == "__main__":
    main()
