#!/usr/bin/env python3
"""Synchronize TagTypeEnum in the structural schema from the ontology model.

Module purpose:
    Reads the openlabel-v2 semantic model (openlabel-v2.yaml) and regenerates
    the TagTypeEnum section in the structural model (openlabel-v2-schema.yaml).
    This keeps the JSON Schema vocabulary in sync with the OWL/SHACL ontology.

Dependencies:
    core: (none — standalone script)
    third-party: pyyaml

Usage:
    python scripts/sync_tag_type_enum.py                       # default paths
    python scripts/sync_tag_type_enum.py --check               # dry-run, exit 1 if out of sync
    python scripts/sync_tag_type_enum.py --ontology X --schema Y  # custom paths
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

# Default paths relative to repository root
DEFAULT_ONTOLOGY = Path("linkml/openlabel-v2/openlabel-v2.yaml")
DEFAULT_SCHEMA = Path("linkml/openlabel-v2/openlabel-v2-schema.yaml")


def extract_tag_types(ontology_path: Path) -> tuple[list[str], dict[str, str]]:
    """Extract all valid tag.type values from the ontology model.

    Returns:
        Tuple of (yaml_lines, stats) where yaml_lines is the TagTypeEnum YAML
        fragment and stats is a dict of category counts.
    """
    with open(ontology_path) as f:
        model = yaml.safe_load(f)

    enums = model.get("enums", {})
    slots = model.get("slots", {})

    # Admin slots
    admin_slots = model["classes"].get("AdminTag", {}).get("slots", [])

    # All enum permissible values (to detect overlaps with boolean flags)
    all_enum_values: set[str] = set()
    for edef in enums.values():
        all_enum_values.update(edef.get("permissible_values", {}).keys())

    # Enum-typed slots (slot names that take enum values — valid tag types in v1)
    enum_names = set(enums.keys())
    enum_slots = [
        sname for sname, sdef in slots.items() if sdef.get("range") in enum_names
    ]

    # Boolean flags — exclude those already in enum values to avoid duplicate keys
    bool_flags = [
        sname
        for sname, sdef in slots.items()
        if sdef.get("range") == "boolean"
        and sname not in all_enum_values
        and sname not in set(enum_slots)
    ]

    # Build YAML lines
    lines: list[str] = []
    lines.append("  TagTypeEnum:")
    lines.append("    description: >-")
    lines.append(
        "      All valid values for the tag.type field in ASAM OpenLABEL v1 format"
    )
    lines.append(
        "      files. Derived from the openlabel-v2 ontology vocabulary (classes,"
    )
    lines.append("      enums, slots). AUTO-GENERATED — do not edit manually.")
    lines.append("    permissible_values:")

    # Structural classes
    lines.append("      # --- Structural class types ---")
    for c in ["Tag", "AdminTag", "Odd", "Behaviour", "RoadUser"]:
        lines.append(f"      {c}:")
        lines.append("        description: Structural class type")

    # Admin properties
    lines.append("      # --- Administration tag properties ---")
    for s in sorted(admin_slots):
        lines.append(f"      {s}:")
        lines.append("        description: Administration tag property")

    # Boolean flags
    lines.append("      # --- Boolean flag tags (ODD/Behaviour) ---")
    for s in sorted(bool_flags):
        lines.append(f"      {s}:")
        lines.append("        description: Boolean ODD/Behaviour flag")

    # Enum-typed slot names
    lines.append("      # --- Enum category tags (slot names with enum ranges) ---")
    for s in sorted(enum_slots):
        slot_range = slots[s].get("range", "")
        lines.append(f"      {s}:")
        lines.append(
            f"        description: Enum category tag (takes values from {slot_range})"
        )

    # Enum values by family
    for ename in sorted(enums.keys()):
        pvs = enums[ename].get("permissible_values", {})
        lines.append(f"      # --- {ename} ---")
        for pv in sorted(pvs.keys()):
            lines.append(f"      {pv}:")
            desc = pvs[pv].get("description", "")
            if desc:
                desc_clean = desc.replace('"', '\\"')
                lines.append(f'        description: "{desc_clean}"')

    # Stats
    all_types: set[str] = set()
    all_types.update(["Tag", "AdminTag", "Odd", "Behaviour", "RoadUser"])
    all_types.update(admin_slots)
    all_types.update(bool_flags)
    all_types.update(enum_slots)
    for edef in enums.values():
        all_types.update(edef.get("permissible_values", {}).keys())

    stats = {
        "total": str(len(all_types)),
        "structural_classes": "5",
        "admin_properties": str(len(admin_slots)),
        "boolean_flags": str(len(bool_flags)),
        "enum_category_slots": str(len(enum_slots)),
        "enum_leaf_values": str(
            sum(len(e.get("permissible_values", {})) for e in enums.values())
        ),
    }

    return lines, stats


def update_schema(schema_path: Path, enum_lines: list[str]) -> bool:
    """Replace the TagTypeEnum section in the schema YAML.

    Returns:
        True if the file was changed, False if already up to date.
    """
    content = schema_path.read_text(encoding="utf-8")

    # Find the TagTypeEnum block boundaries
    marker_start = "  TagTypeEnum:"
    start_idx = content.find(marker_start)
    if start_idx == -1:
        raise ValueError(f"Could not find '{marker_start}' in {schema_path}")

    # Find the end of the TagTypeEnum block (next top-level enum or end of file)
    lines = content[start_idx:].split("\n")
    end_offset = 0
    in_enum = False
    for i, line in enumerate(lines):
        if i == 0:
            in_enum = True
            continue
        # A line at indentation level 2 (or less) that isn't empty marks the end
        stripped = line.rstrip()
        if stripped and not stripped.startswith(" " * 6) and not stripped.startswith(
            "    "
        ):
            # This is at enum level or higher — we've left TagTypeEnum
            end_offset = i
            break
        if (
            in_enum
            and stripped
            and not stripped.startswith("#")
            and len(stripped) > 0
        ):
            # Check if this is a new enum at level 2 (2 spaces)
            if stripped.startswith("  ") and not stripped.startswith(
                "    "
            ):
                if stripped != marker_start.strip():
                    end_offset = i
                    break

    if end_offset == 0:
        # TagTypeEnum goes to end of file
        new_content = content[:start_idx] + "\n".join(enum_lines) + "\n"
    else:
        remaining = "\n".join(lines[end_offset:])
        new_content = content[:start_idx] + "\n".join(enum_lines) + "\n" + remaining

    if new_content == content:
        return False

    schema_path.write_text(new_content, encoding="utf-8")
    return True


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync TagTypeEnum from ontology model to structural schema."
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=DEFAULT_ONTOLOGY,
        help=f"Path to ontology model YAML (default: {DEFAULT_ONTOLOGY})",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Path to structural schema YAML (default: {DEFAULT_SCHEMA})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry run: exit 1 if enum is out of sync, 0 if up to date.",
    )
    args = parser.parse_args()

    if not args.ontology.exists():
        print(f"ERROR: Ontology model not found: {args.ontology}", file=sys.stderr)
        return 1
    if not args.schema.exists():
        print(f"ERROR: Schema model not found: {args.schema}", file=sys.stderr)
        return 1

    enum_lines, stats = extract_tag_types(args.ontology)
    print(
        f"TagTypeEnum: {stats['total']} values "
        f"({stats['structural_classes']} classes, "
        f"{stats['admin_properties']} admin, "
        f"{stats['boolean_flags']} boolean, "
        f"{stats['enum_category_slots']} enum slots, "
        f"{stats['enum_leaf_values']} enum values)"
    )

    if args.check:
        # Read current content and compare
        content = args.schema.read_text(encoding="utf-8")
        expected_block = "\n".join(enum_lines)
        if expected_block in content:
            print("TagTypeEnum is up to date.")
            return 0
        else:
            print("TagTypeEnum is OUT OF SYNC — run without --check to update.")
            return 1

    changed = update_schema(args.schema, enum_lines)
    if changed:
        print(f"Updated TagTypeEnum in {args.schema}")
    else:
        print("TagTypeEnum already up to date — no changes needed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
