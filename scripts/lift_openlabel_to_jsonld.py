#!/usr/bin/env python3
"""Re-model ASAM OpenLABEL tagging JSON into the ontology's flat JSON-LD shape.

.. deprecated::
    This script implements the SUPERSEDED modelling approach and is scheduled
    for removal. See issue #129.

    Despite the name it does **not** perform a version conversion — input and
    output are both ASAM OpenLABEL v1.0.0 content. Nor is it a JSON-LD *lift*:
    it discards the ASAM document structure and rebuilds a bespoke flat shape
    that matches ``openlabel-tagging.yaml`` (the ontology model), because that
    model currently has no structural spine of its own.

    It is **lossy**. The following are dropped:

    - the ``openlabel`` root wrapper
    - every tag UID (the ``tags`` dict keys)
    - ``ontology_uid`` and ``resource_uid``
    - all of ``metadata`` except ``tagged_file``
    - any tag whose type is unmapped (reported under ``_unmapped_tags``)

    Consequently the fixtures it produces match the ontology *by construction*,
    which is why the SHACL layer has never validated a real ASAM file (#129).

    Once the ontology model accepts the ASAM shape, lifting becomes trivial —
    add ``@context`` and ``@type`` to the file and nothing else — and this
    script should be deleted along with the tests that shell out to it.

Module purpose:
    Transforms plain ASAM OpenLABEL scenario tagging JSON files (generic
    tag.type + tag_data containers) into JSON-LD documents using the
    openlabel-tagging ontology context, for SHACL validation.

Dependencies:
    core: (none — standalone script)
    third-party: pyyaml

Usage:
    python scripts/lift_openlabel_to_jsonld.py input.json
    python scripts/lift_openlabel_to_jsonld.py input.json -o output.jsonld
    python scripts/lift_openlabel_to_jsonld.py input.json --context-uri https://...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

DEFAULT_CONTEXT_URI = "https://w3id.org/ascs-ev/envited-x/openlabel/v1.1.0-alpha/"
DEFAULT_ONTOLOGY = Path("linkml/openlabel-tagging/openlabel-tagging.yaml")

# Maps ASAM tag.type -> ontology class + slot
# Built from the ontology model at runtime


def load_tag_mapping(
    ontology_path: Path,
) -> dict[str, dict[str, str]]:
    """Load the mapping from ASAM tag.type values to ontology typed slots.

    Returns:
        Dict mapping tag.type string to {class, slot, range} info.
    """
    with open(ontology_path, encoding="utf-8") as f:
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


def extract_tag_value(
    tag: dict, tag_mapping: dict[str, dict[str, str]]
) -> str | bool | float | None:
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


def _assign_slot(
    target: dict[str, str | bool | float | list | None],
    slot: str,
    value: str | bool | float | None,
) -> None:
    """Assign ``value`` to ``slot``, accumulating into a list on repeats.

    Multiple v1 tags can map to the same class+slot (e.g. several values of one
    enum category, which the ontology model represents as an array). Promote to a list
    instead of silently overwriting so no tag value is lost.
    """
    if slot not in target:
        target[slot] = value
        return
    existing = target[slot]
    if isinstance(existing, list):
        if value not in existing:
            existing.append(value)
    elif existing != value:
        target[slot] = [existing, value]


def remodel_to_ontology_shape(
    asam_data: dict,
    tag_mapping: dict[str, dict[str, str]],
    context_uri: str = DEFAULT_CONTEXT_URI,
) -> dict:
    """Re-model an ASAM OpenLABEL JSON into the ontology's flat JSON-LD shape.

    Lossy by construction — see the module docstring and issue #129.

    Args:
        asam_data: The parsed ASAM OpenLABEL JSON content.
        tag_mapping: Mapping from tag.type to ontology slot info.
        context_uri: The JSON-LD @context URI to inject.

    Returns:
        A JSON-LD document with typed slots, matching the ontology model.
    """
    openlabel = asam_data.get("openlabel", asam_data)
    tags = openlabel.get("tags", {})
    metadata = openlabel.get("metadata", {})

    # Group tags by their ontology class
    class_slots: dict[str, dict[str, str | bool | float | list | None]] = {}
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

        class_slots.setdefault(cls, {})
        _assign_slot(class_slots[cls], slot, value)

    # Build the flat JSON-LD document
    result: dict = {
        "@context": context_uri,
        "@type": "Tag",
    }

    # Add metadata as comment if present
    if metadata.get("tagged_file"):
        result["@id"] = f"urn:openlabel:{metadata.get('tagged_file', 'unknown')}"

    # Build class objects. The ODD sub-hierarchy (OddScenery, OddEnvironment,
    # OddDynamicElements) collapses into a single "Odd" object; every other class
    # is emitted as its own typed object.
    odd_classes = {"Odd", "OddScenery", "OddEnvironment", "OddDynamicElements"}
    for cls_name, slot_values in sorted(class_slots.items()):
        if cls_name in odd_classes:
            result.setdefault("Odd", {"@type": "Odd"}).update(slot_values)
        else:
            result[cls_name] = {"@type": cls_name, **slot_values}

    # Report unmapped tags
    if unmapped:
        result["_unmapped_tags"] = unmapped

    return result


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Re-model ASAM OpenLABEL tagging JSON into the ontology's flat JSON-LD shape. DEPRECATED - see issue #129."
    )
    parser.add_argument("input", type=Path, help="Input ASAM OpenLABEL JSON file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON-LD file (default: stdout)",
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
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pretty-print JSON output (use --no-pretty for compact output).",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        return 1
    if not args.ontology.exists():
        print(f"ERROR: Ontology model not found: {args.ontology}", file=sys.stderr)
        return 1

    # Load input
    with open(args.input, encoding="utf-8") as f:
        asam_data = json.load(f)

    # Load mapping
    tag_mapping = load_tag_mapping(args.ontology)

    # Re-model
    out_data = remodel_to_ontology_shape(asam_data, tag_mapping, args.context_uri)

    # Output
    indent = 2 if args.pretty else None
    output_json = json.dumps(out_data, indent=indent, ensure_ascii=False)

    if args.output:
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"Wrote {args.input} -> {args.output}")
    else:
        print(output_json)

    # Report unmapped tags
    if "_unmapped_tags" in out_data:
        count = len(out_data["_unmapped_tags"])
        print(
            f"\nWARNING: {count} tag(s) could not be mapped to ontology slots:",
            file=sys.stderr,
        )
        for t in out_data["_unmapped_tags"]:
            print(f"  - {t['type']} (uid: {t['uid']})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
