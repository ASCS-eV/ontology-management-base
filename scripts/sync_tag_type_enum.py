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
    with open(ontology_path, encoding="utf-8") as f:
        model = yaml.safe_load(f)

    enums = model.get("enums", {})
    slots = model.get("slots", {})
    classes = model.get("classes", {})

    # Tag classes: every class minted in the openlabel-v2 namespace forms the
    # ASAM v1 tag hierarchy (structural roots + category nodes). Helper classes
    # outside that namespace (e.g. sdo:QuantitativeValue) are excluded.
    tag_classes = sorted(
        cname
        for cname, cdef in classes.items()
        if str(cdef.get("class_uri", "")).startswith("openlabel_v2:")
    )

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

    # Tag classes (structural roots + hierarchy category nodes)
    lines.append("      # --- Tag classes (hierarchy nodes) ---")
    for c in tag_classes:
        lines.append(f"      {c}:")
        lines.append("        description: Tag class (hierarchy node)")

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
    all_types.update(tag_classes)
    all_types.update(admin_slots)
    all_types.update(bool_flags)
    all_types.update(enum_slots)
    for edef in enums.values():
        all_types.update(edef.get("permissible_values", {}).keys())

    stats = {
        "total": str(len(all_types)),
        "structural_classes": str(len(tag_classes)),
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
    lines = content.split("\n")

    # Locate the TagTypeEnum block. The block body is indented >= 4 spaces (its
    # `description:`/`permissible_values:` keys) or 6 spaces (value comments);
    # the block ends at the first subsequent non-blank line indented <= 2 spaces
    # (a sibling enum at indent 2, or a top-level key at indent 0). This is
    # position-independent — TagTypeEnum need not be the last enum in the file.
    marker = "  TagTypeEnum:"
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == marker)
    except StopIteration as exc:
        raise ValueError(f"Could not find '{marker}' in {schema_path}") from exc

    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= 2:
            end = i
            break

    new_lines = lines[:start] + enum_lines + lines[end:]
    new_content = "\n".join(new_lines)
    # Preserve the file's trailing newline when TagTypeEnum is the final block.
    if not new_content.endswith("\n"):
        new_content += "\n"

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
