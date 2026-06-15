#!/usr/bin/env python3
"""Convert ASAM OpenLABEL v1 JSON files to JSON-LD with v2 context.

Module purpose:
    Transforms plain ASAM OpenLABEL scenario tagging JSON files (v1 format with
    generic tag.type + tag_data containers) into JSON-LD documents that use the
    openlabel-v2 ontology context for type coercion and SHACL validation.

Dependencies:
    core: (none — standalone script)
    third-party: pyyaml

Usage:
    python scripts/convert_openlabel_v1_to_v2.py input.json
    python scripts/convert_openlabel_v1_to_v2.py input.json -o output.jsonld
    python scripts/convert_openlabel_v1_to_v2.py input.json --context-uri https://...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

DEFAULT_CONTEXT_URI = "https://w3id.org/ascs-ev/envited-x/openlabel/v2/"
DEFAULT_ONTOLOGY = Path("linkml/openlabel-v2/openlabel-v2.yaml")

# Maps v1 tag.type → v2 class + slot
# Built from the ontology model at runtime


def load_tag_mapping(
    ontology_path: Path,
) -> dict[str, dict[str, str]]:
    """Load the mapping from v1 tag.type values to v2 typed slots.

    Returns:
        Dict mapping tag.type string to {class, slot, range} info.
    """
    with open(ontology_path) as f:
        model = yaml.safe_load(f)

    slots = model.get("slots", {})
    enums = model.get("enums", {})
    classes = model.get("classes", {})
    enum_names = set(enums.keys())

    mapping: dict[str, dict[str, str]] = {}

    # Build reverse index: which class owns which slot
    slot_owners: dict[str, str] = {}
    for cls_name, cls_def in classes.items():
        for slot_name in cls_def.get("slots", []):
            slot_owners[slot_name] = cls_name

    # Boolean flag slots
    for sname, sdef in slots.items():
        if sdef.get("range") == "boolean":
            owner = slot_owners.get(sname, "unknown")
            mapping[sname] = {
                "class": owner,
                "slot": sname,
                "range": "boolean",
                "type": "flag",
            }

    # Enum-typed slots and their values
    for sname, sdef in slots.items():
        slot_range = sdef.get("range", "")
        if slot_range in enum_names:
            owner = slot_owners.get(sname, "unknown")
            mapping[sname] = {
                "class": owner,
                "slot": sname,
                "range": slot_range,
                "type": "enum_slot",
            }
            # Each enum value is also a valid tag.type
            pvs = enums[slot_range].get("permissible_values", {})
            for pv_name in pvs:
                mapping[pv_name] = {
                    "class": owner,
                    "slot": sname,
                    "range": slot_range,
                    "type": "enum_value",
                    "value": pv_name,
                }

    # Admin slots (string-typed properties)
    admin_slots = classes.get("AdminTag", {}).get("slots", [])
    for sname in admin_slots:
        if sname not in mapping:
            sdef = slots.get(sname, {})
            mapping[sname] = {
                "class": "AdminTag",
                "slot": sname,
                "range": sdef.get("range", "string"),
                "type": "admin",
            }

    return mapping


def extract_tag_value(tag: dict, tag_mapping: dict[str, dict[str, str]]) -> str | bool | float | None:
    """Extract the value from tag_data for a given tag.

    For boolean flags: True (presence = true)
    For enum values: the enum value string
    For admin tags with tag_data.text: the text value
    For numeric tags with tag_data.num: the numeric value
    """
    tag_type = tag.get("type", "")
    info = tag_mapping.get(tag_type, {})
    tag_data = tag.get("tag_data", {})

    if info.get("type") == "flag":
        return True

    if info.get("type") == "enum_value":
        return info.get("value", tag_type)

    if info.get("type") == "enum_slot":
        return True

    if info.get("type") == "admin":
        # Admin tags typically carry text values
        texts = tag_data.get("text", [])
        if texts and isinstance(texts, list) and len(texts) > 0:
            return texts[0].get("val", "")
        return ""

    # For numeric values
    nums = tag_data.get("num", [])
    if nums and isinstance(nums, list) and len(nums) > 0:
        return nums[0].get("val")

    # For boolean values
    bools = tag_data.get("boolean", [])
    if bools and isinstance(bools, list) and len(bools) > 0:
        return bools[0].get("val")

    return True


def convert_v1_to_v2(
    v1_data: dict,
    tag_mapping: dict[str, dict[str, str]],
    context_uri: str = DEFAULT_CONTEXT_URI,
) -> dict:
    """Convert a v1 OpenLABEL JSON to v2 JSON-LD format.

    Args:
        v1_data: The parsed v1 JSON content.
        tag_mapping: Mapping from tag.type to v2 slot info.
        context_uri: The JSON-LD @context URI to inject.

    Returns:
        A v2 JSON-LD document with typed slots.
    """
    openlabel = v1_data.get("openlabel", v1_data)
    tags = openlabel.get("tags", {})
    metadata = openlabel.get("metadata", {})

    # Group tags by their v2 class
    class_slots: dict[str, dict[str, str | bool | float | None]] = {}
    unmapped: list[dict] = []

    for tag_uid, tag in tags.items():
        tag_type = tag.get("type", "")
        info = tag_mapping.get(tag_type)

        if not info:
            unmapped.append({"uid": tag_uid, "type": tag_type})
            continue

        cls = info["class"]
        slot = info["slot"]
        value = extract_tag_value(tag, tag_mapping)

        if cls not in class_slots:
            class_slots[cls] = {}

        # For enum values, the slot is the enum category slot
        if info["type"] == "enum_value":
            class_slots[cls][slot] = value
        else:
            class_slots[cls][slot] = value

    # Build the v2 JSON-LD document
    result: dict = {
        "@context": context_uri,
        "@type": "Tag",
    }

    # Add metadata as comment if present
    if metadata.get("tagged_file"):
        result["@id"] = f"urn:openlabel:{metadata.get('tagged_file', 'unknown')}"

    # Build class objects
    for cls_name, slot_values in sorted(class_slots.items()):
        if cls_name == "AdminTag":
            result[cls_name] = {
                "@type": cls_name,
                **slot_values,
            }
        elif cls_name in ("Odd", "OddScenery", "OddEnvironment", "OddDynamicElements"):
            if "Odd" not in result:
                result["Odd"] = {"@type": "Odd"}
            result["Odd"].update(slot_values)
        elif cls_name == "Behaviour":
            result[cls_name] = {
                "@type": cls_name,
                **slot_values,
            }
        elif cls_name == "RoadUser":
            result[cls_name] = {
                "@type": cls_name,
                **slot_values,
            }
        else:
            result[cls_name] = {
                "@type": cls_name,
                **slot_values,
            }

    # Report unmapped tags
    if unmapped:
        result["_unmapped_tags"] = unmapped

    return result


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert ASAM OpenLABEL v1 JSON to v2 JSON-LD format."
    )
    parser.add_argument("input", type=Path, help="Input v1 JSON file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output v2 JSON-LD file (default: stdout)",
    )
    parser.add_argument(
        "--context-uri",
        default=DEFAULT_CONTEXT_URI,
        help=f"JSON-LD @context URI (default: {DEFAULT_CONTEXT_URI})",
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=DEFAULT_ONTOLOGY,
        help=f"Path to ontology model YAML (default: {DEFAULT_ONTOLOGY})",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        return 1
    if not args.ontology.exists():
        print(f"ERROR: Ontology model not found: {args.ontology}", file=sys.stderr)
        return 1

    # Load input
    with open(args.input) as f:
        v1_data = json.load(f)

    # Load mapping
    tag_mapping = load_tag_mapping(args.ontology)

    # Convert
    v2_data = convert_v1_to_v2(v1_data, tag_mapping, args.context_uri)

    # Output
    indent = 2 if args.pretty else None
    output_json = json.dumps(v2_data, indent=indent, ensure_ascii=False)

    if args.output:
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"Converted {args.input} → {args.output}")
    else:
        print(output_json)

    # Report unmapped tags
    if "_unmapped_tags" in v2_data:
        count = len(v2_data["_unmapped_tags"])
        print(
            f"\nWARNING: {count} tag(s) could not be mapped to v2 slots:",
            file=sys.stderr,
        )
        for t in v2_data["_unmapped_tags"]:
            print(f"  - {t['type']} (uid: {t['uid']})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
