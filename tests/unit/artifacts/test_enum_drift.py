#!/usr/bin/env python3
"""
Drift guard for the ASAM enumerations transcribed into SHACL ``sh:in`` lists.

Every ``sh:in`` in this repository that claims to model an ASAM enumeration must stay
set-equal to that enumeration in the source this repository pins. Five such lists were
silently wrong before #91 — a truncated alphabetical sort, an incomplete OSI trace-type
set, an undeclared extension — and each one was findable by set arithmetic alone.

The contracts below make that arithmetic executable, so a submodule or schema bump that
changes an enumeration fails the build instead of drifting unnoticed.

Sources of truth:

* ASAM OpenDRIVE V1.8.0 XSD ``simpleType`` enumerations in ``imports/OpenDrive/xsd_schema/``.
  These also carry ``<xs:documentation>deprecated</xs:documentation>`` per value.
* ASAM OpenDRIVE v1.9.0 specification §11.8, which deprecates two further lane types that
  the pinned XSD does *not* mark. Deprecation therefore has two sources and each value
  records which one deprecates it.
* ASAM OSI v3.8.0 ``doc/architecture/trace_file_naming.adoc`` for the single-channel
  trace file types.

Two things are deliberately *not* derived from a pinned source, and say so:

* ``truck`` — not an ``e_objectType`` in any pinned schema; an ENVITED-X extension.
* ``hdmap``'s v1.4 and v1.5–1.7 branches — this repository pins only V1.8.0 schemas, so
  the historical sets are frozen snapshots checked against themselves, not against ASAM.
"""

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Sequence, Tuple

import pytest
from rdflib import RDF, Graph, URIRef

ROOT = Path(__file__).resolve().parents[3]

XS = "{http://www.w3.org/2001/XMLSchema}"
SH = "http://www.w3.org/ns/shacl#"

LANE_XSD = "imports/OpenDrive/xsd_schema/OpenDRIVE_Lane.xsd"
OBJECT_XSD = "imports/OpenDrive/xsd_schema/OpenDRIVE_Object.xsd"
ROAD_XSD = "imports/OpenDrive/xsd_schema/OpenDRIVE_Road.xsd"

OSI_NAMING_ADOC = (
    "submodules/asam-openx-standards/submodules/open-simulation-interface"
    "/doc/architecture/trace_file_naming.adoc"
)

# Which document deprecates a value. The pinned XSD and the v1.9.0 prose disagree, so the
# distinction is recorded rather than flattened into one set.
XSD = "ASAM OpenDRIVE V1.8.0 XSD <xs:documentation>deprecated</xs:documentation>"
SPEC_11_8 = "ASAM OpenDRIVE v1.9.0 specification §11.8"


# =============================================================================
# Source readers
# =============================================================================


def _xsd_enumeration(
    rel_path: str, type_name: str
) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """Return ``(values, deprecated)`` of an XSD ``simpleType`` enumeration."""
    root = ET.parse(ROOT / rel_path).getroot()
    for simple_type in root.iter(f"{XS}simpleType"):
        if simple_type.get("name") != type_name:
            continue
        values, deprecated = set(), set()
        for enum in simple_type.iter(f"{XS}enumeration"):
            value = enum.get("value")
            values.add(value)
            docs = " ".join(
                (doc.text or "") for doc in enum.iter(f"{XS}documentation")
            ).lower()
            if "deprecated" in docs:
                deprecated.add(value)
        return frozenset(values), frozenset(deprecated)
    raise AssertionError(f"simpleType {type_name!r} not found in {rel_path}")


def _require_osi_specification() -> Path:
    """Locate the pinned OSI naming conventions, or fail where they are guaranteed.

    The file lives in a nested submodule, so a missing checkout is a legitimate local
    state and skipping is the right answer there. Where the sources *are* guaranteed —
    the ``Pinned Standards Drift`` job, which initialises the submodule and sets
    ``OMB_REQUIRE_PINNED_SOURCES=1`` — a missing file must fail instead: a drift guard
    that quietly stops running is worse than no guard.
    """
    path = ROOT / OSI_NAMING_ADOC
    if path.exists():
        return path
    if os.environ.get("OMB_REQUIRE_PINNED_SOURCES"):
        raise AssertionError(
            f"{OSI_NAMING_ADOC} is missing while OMB_REQUIRE_PINNED_SOURCES is set. "
            "Initialise the ASAM standards submodule (git submodule update --init "
            "--recursive submodules/asam-openx-standards) so this guard actually runs."
        )
    pytest.skip(
        "ASAM OSI submodule not checked out; run "
        "'git submodule update --init --recursive submodules/asam-openx-standards'"
    )


def _osi_trace_types() -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """Return ``(single_channel_types, abbreviations)`` from the OSI naming conventions.

    The document lists eleven abbreviations: the ten single-channel message types plus
    ``multi``, which denotes the multi-channel container and has no message type of its
    own. Parsing naively and comparing against ``ositrace:formatType`` would fail 11 to 10,
    so ``multi`` is excluded here and that exclusion is asserted below.
    """
    text = _require_osi_specification().read_text(encoding="utf-8")
    abbreviations, message_types = set(), set()
    for abbrev, description in re.findall(r"^`([a-z]+)`::\n(.+)$", text, re.MULTILINE):
        abbreviations.add(abbrev)
        match = re.search(r"contains `(\w+)` messages", description)
        if match:
            message_types.add(match.group(1))
    return frozenset(message_types), frozenset(abbreviations)


# =============================================================================
# SHACL readers
# =============================================================================


def _shacl_graph(domain: str) -> Graph:
    graph = Graph()
    graph.parse(ROOT / "artifacts" / domain / f"{domain}.shacl.ttl", format="turtle")
    return graph


def _local_name(term: URIRef) -> str:
    return re.split(r"[/#]", str(term))[-1]


def _path_local_names(graph: Graph, shape) -> Tuple[str, ...]:
    """Local names of a ``sh:path``, whether a single property or a sequence path."""
    path = graph.value(shape, URIRef(SH + "path"))
    if (path, RDF.first, None) in graph:
        return tuple(_local_name(step) for step in graph.items(path))
    return (_local_name(path),)


def _sh_in(graph: Graph, shape) -> Optional[FrozenSet[str]]:
    values = graph.value(shape, URIRef(SH + "in"))
    if values is None:
        return None
    return frozenset(str(value) for value in graph.items(values))


def _sh_in_sets(graph: Graph, path: Sequence[str]) -> Tuple[FrozenSet[str], ...]:
    """Every ``sh:in`` list declared on property shapes with this ``sh:path``.

    ``hdmap`` declares the same path once per version branch, so this returns one set per
    branch; ``ositrace`` declares each path once.
    """
    found = []
    for shape in set(graph.subjects(URIRef(SH + "path"), None)):
        if _path_local_names(graph, shape) != tuple(path):
            continue
        values = _sh_in(graph, shape)
        if values is not None:
            found.append(values)
    return tuple(found)


def _descriptions(graph: Graph, path: Sequence[str]) -> str:
    texts = []
    for shape in set(graph.subjects(URIRef(SH + "path"), None)):
        if _path_local_names(graph, shape) != tuple(path):
            continue
        for description in graph.objects(shape, URIRef(SH + "description")):
            texts.append(str(description))
    return " ".join(texts)


# =============================================================================
# Contracts
# =============================================================================


@dataclass(frozen=True)
class Contract:
    """One ``sh:in`` list that claims to model an ASAM enumeration."""

    domain: str
    path: Tuple[str, ...]
    source: Tuple[str, str]
    extensions: Dict[str, str] = field(default_factory=dict)
    deprecated: Dict[str, str] = field(default_factory=dict)
    # ``hdmap`` states the version branches in comments, not in per-branch descriptions,
    # so only the shapes that carry a description are checked for deprecation notes.
    documents_deprecation: bool = False

    @property
    def id(self) -> str:
        return f"{self.domain}:{'/'.join(self.path)}"


LANE_DEPRECATED = {
    "mwyEntry": XSD,
    "mwyExit": XSD,
    "special1": XSD,
    "special2": XSD,
    "special3": XSD,
    "sidewalk": SPEC_11_8,
    "bidirectional": SPEC_11_8,
}

OBJECT_DEPRECATED = {
    value: XSD
    for value in (
        "car",
        "bus",
        "trailer",
        "bike",
        "motorbike",
        "tram",
        "train",
        "pedestrian",
        "wind",
    )
}

TRUCK_RATIONALE = (
    "Not an ASAM OpenDRIVE e_objectType in any schema pinned by this repository; it "
    "occurs only in e_road_objects_object_parkingSpace_access. ENVITED-X ecosystem "
    "extension kept for backward compatibility (see #48)."
)

CONTRACTS = (
    Contract(
        domain="ositrace",
        path=("roadTypes",),
        source=(ROAD_XSD, "e_roadType"),
    ),
    Contract(
        domain="ositrace",
        path=("laneTypes",),
        source=(LANE_XSD, "e_laneType"),
        deprecated=LANE_DEPRECATED,
        documents_deprecation=True,
    ),
    Contract(
        domain="ositrace",
        path=("levelOfDetail",),
        source=(OBJECT_XSD, "e_objectType"),
        extensions={"truck": TRUCK_RATIONALE},
        deprecated=OBJECT_DEPRECATED,
        documents_deprecation=True,
    ),
    Contract(
        domain="hdmap",
        path=("hasContent", "roadTypes"),
        source=(ROAD_XSD, "e_roadType"),
    ),
    Contract(
        domain="hdmap",
        path=("hasContent", "laneTypes"),
        source=(LANE_XSD, "e_laneType"),
        deprecated=LANE_DEPRECATED,
    ),
    Contract(
        domain="hdmap",
        path=("hasContent", "levelOfDetail"),
        source=(OBJECT_XSD, "e_objectType"),
        extensions={"truck": TRUCK_RATIONALE},
        deprecated=OBJECT_DEPRECATED,
    ),
)

# ``hdmap`` dispatches on the OpenDRIVE revision, but this repository pins only the
# V1.8.0 schemas. The historical sets therefore cannot be derived from a pinned source;
# they are frozen snapshots, transcribed from the revisions named below, and are checked
# against themselves so an accidental edit still fails the build.
HISTORICAL_BRANCHES = {
    ("hdmap", "roadTypes", "v1.4"): frozenset(
        {"bicycle", "lowSpeed", "motorway", "pedestrian", "rural", "town", "unknown"}
    ),
    ("hdmap", "laneTypes", "v1.4"): frozenset(
        {
            "bidirectional",
            "biking",
            "border",
            "driving",
            "entry",
            "exit",
            "median",
            "none",
            "offRamp",
            "onRamp",
            "parking",
            "rail",
            "restricted",
            "roadWorks",
            "shoulder",
            "sidewalk",
            "special1",
            "special2",
            "special3",
            "stop",
            "tram",
        }
    ),
    ("hdmap", "laneTypes", "v1.5-v1.7"): frozenset(
        {
            "HOV",
            "bidirectional",
            "biking",
            "border",
            "bus",
            "connectingRamp",
            "driving",
            "entry",
            "exit",
            "median",
            "mwyEntry",
            "mwyExit",
            "none",
            "offRamp",
            "onRamp",
            "parking",
            "rail",
            "restricted",
            "roadWorks",
            "shoulder",
            "sidewalk",
            "special1",
            "special2",
            "special3",
            "stop",
            "taxi",
            "tram",
        }
    ),
}


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c.id)
def test_enum_equals_pinned_source_plus_declared_extensions(contract: Contract):
    """The widest ``sh:in`` for a path equals the pinned enumeration plus extensions.

    "Widest" because ``hdmap`` declares one branch per OpenDRIVE revision and only the
    current-revision branch is expected to match the pinned V1.8.0 schema; the historical
    branches are covered by ``test_historical_branches_match_frozen_snapshots``.
    """
    graph = _shacl_graph(contract.domain)
    declared = _sh_in_sets(graph, contract.path)
    assert declared, f"no sh:in found for {contract.id}"

    expected = _xsd_enumeration(*contract.source)[0] | frozenset(contract.extensions)
    widest = max(declared, key=len)

    assert widest == expected, (
        f"{contract.id} drifted from {contract.source[1]} in {contract.source[0]}:\n"
        f"  missing: {sorted(expected - widest)}\n"
        f"  unexpected: {sorted(widest - expected)}"
    )


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c.id)
def test_extensions_are_declared_with_a_rationale(contract: Contract):
    """Values not in the pinned source exist only where declared, and say why."""
    graph = _shacl_graph(contract.domain)
    pinned = _xsd_enumeration(*contract.source)[0]
    widest = max(_sh_in_sets(graph, contract.path), key=len)

    declared = frozenset(contract.extensions)
    assert (widest - pinned) == declared, (
        f"{contract.id} extension set changed:\n"
        f"  undeclared non-ASAM values: {sorted((widest - pinned) - declared)}\n"
        f"  declared but no longer present: {sorted(declared - widest)}"
    )
    for value, rationale in contract.extensions.items():
        assert len(rationale) > 40, f"{contract.id}: {value!r} needs a real rationale"


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c.id)
def test_deprecated_values_stay_accepted(contract: Contract):
    """Deprecated is not removed: every deprecated value must still validate.

    Also checks that the XSD half of the deprecation map is exactly what the pinned schema
    marks, so a bump that deprecates a new value fails until the map and the descriptions
    are updated.
    """
    graph = _shacl_graph(contract.domain)
    widest = max(_sh_in_sets(graph, contract.path), key=len)

    missing = frozenset(contract.deprecated) - widest
    assert not missing, (
        f"{contract.id} no longer accepts deprecated {sorted(missing)}; existing "
        "self-descriptions using them would become invalid"
    )

    xsd_marked = _xsd_enumeration(*contract.source)[1]
    declared_from_xsd = {v for v, src in contract.deprecated.items() if src == XSD}
    assert xsd_marked == declared_from_xsd, (
        f"{contract.id}: the pinned schema's deprecation set changed:\n"
        f"  newly deprecated: {sorted(xsd_marked - declared_from_xsd)}\n"
        f"  no longer deprecated: {sorted(declared_from_xsd - xsd_marked)}"
    )


@pytest.mark.parametrize(
    "contract",
    [c for c in CONTRACTS if c.documents_deprecation],
    ids=lambda c: c.id,
)
def test_deprecated_values_are_named_in_the_description(contract: Contract):
    """The shape must tell an author which accepted values are deprecated."""
    description = _descriptions(_shacl_graph(contract.domain), contract.path)
    assert "deprecat" in description.lower(), f"{contract.id} has no deprecation note"

    unnamed = [value for value in contract.deprecated if value not in description]
    assert not unnamed, (
        f"{contract.id} accepts deprecated values without naming them in its "
        f"sh:description: {sorted(unnamed)}"
    )


@pytest.mark.parametrize(
    "key,expected",
    sorted(HISTORICAL_BRANCHES.items()),
    ids=lambda k: "-".join(k) if isinstance(k, tuple) else None,
)
def test_historical_branches_match_frozen_snapshots(key, expected: FrozenSet[str]):
    """The pre-v1.8 OpenDRIVE branches equal their declared snapshots.

    Not verified against ASAM: only V1.8.0 schemas are pinned here, so these sets are
    transcriptions that this test freezes rather than validates.
    """
    domain, path_tail, _revision = key
    declared = _sh_in_sets(_shacl_graph(domain), ("hasContent", path_tail))
    assert expected in declared, (
        f"{domain}:{path_tail} no longer declares the {_revision} snapshot; "
        f"branch sizes present: {sorted(len(s) for s in declared)}"
    )


def test_ositrace_formattype_matches_the_osi_trace_types():
    """``formatType`` is the complete set of OSI single-channel trace file types."""
    message_types, abbreviations = _osi_trace_types()

    assert len(abbreviations) == 11 and "multi" in abbreviations, (
        "trace_file_naming.adoc changed shape; it is expected to list ten single-channel "
        f"types plus 'multi'. Found: {sorted(abbreviations)}"
    )
    assert len(message_types) == 10, sorted(message_types)

    declared = _sh_in_sets(_shacl_graph("ositrace"), ("formatType",))
    assert len(declared) == 1, f"expected one formatType sh:in, found {len(declared)}"

    expected = frozenset(f"ASAM OSI {t}" for t in message_types)
    assert declared[0] == expected, (
        "ositrace:formatType is not the complete OSI single-channel trace type set:\n"
        f"  missing: {sorted(expected - declared[0])}\n"
        f"  unexpected: {sorted(declared[0] - expected)}"
    )


def test_ositrace_formattype_and_messagetype_stay_in_bijection():
    """``formatType == "ASAM OSI " + messageType`` — the two encodings cannot drift.

    ``ositrace`` models the same ten OSI types twice: prefixed on
    ``SingleChannelFormatShape`` and bare on ``ChannelShape``. Unifying them is a
    major-version change, so until then they must at least stay equivalent.
    """
    graph = _shacl_graph("ositrace")
    format_types = _sh_in_sets(graph, ("formatType",))[0]
    message_types = _sh_in_sets(graph, ("messageType",))[0]

    assert format_types == frozenset(f"ASAM OSI {t}" for t in message_types), (
        "formatType and messageType disagree:\n"
        f"  formatType without a messageType: "
        f"{sorted(format_types - {f'ASAM OSI {t}' for t in message_types})}\n"
        f"  messageType without a formatType: "
        f"{sorted(t for t in message_types if f'ASAM OSI {t}' not in format_types)}"
    )
