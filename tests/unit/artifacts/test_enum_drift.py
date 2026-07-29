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

* ASAM OpenDRIVE V1.9.0 XSD ``simpleType`` enumerations, pinned in the standards
  submodule. These also carry ``<xs:documentation>deprecated</xs:documentation>`` per value.
* ASAM OpenDRIVE v1.9.0 specification §11.8, which deprecates ``bidirectional`` although
  the pinned XSD does *not* mark it. Deprecation therefore has two sources and each value
  records which one deprecates it.
* ASAM OpenSCENARIO XML V1.4.0 for ``scenario:entityTypes``, which models the union of
  three enumerations (vehicle, pedestrian and misc-object categories).
* ASAM OSI v3.8.0 ``doc/architecture/trace_file_naming.adoc`` for the single-channel
  trace file types.

Two things are deliberately *not* derived from a pinned source, and say so:

* ``truck`` — not an ``e_objectType`` in any pinned schema; an ENVITED-X extension.
* ``hdmap``'s v1.4 and v1.5–1.7 branches — only the current revision's schemas are
  pinned, so the historical sets are frozen snapshots checked against themselves.
"""

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Sequence, Tuple

import pytest
from rdflib import RDF, Graph, URIRef

from omb.core.constants import (
    ASAM_OPENDRIVE_SCHEMA_DIR,
    ASAM_OPENSCENARIO_SCHEMA_FILE,
    ASAM_SUBMODULE_HINT,
)
from omb.utils.xsd_enum_extractor import extract_enums_from_dir
from omb.utils.xsd_shacl_sync import (
    HDMAP_ENUM_MAPPINGS,
    OSITRACE_ENUM_MAPPINGS,
    SCENARIO_ENUM_MAPPINGS,
    run_sync_check,
)

ROOT = Path(__file__).resolve().parents[3]

SH = "http://www.w3.org/ns/shacl#"

LANE_XSD = f"{ASAM_OPENDRIVE_SCHEMA_DIR}/OpenDRIVE_Lane.xsd"
OBJECT_XSD = f"{ASAM_OPENDRIVE_SCHEMA_DIR}/OpenDRIVE_Object.xsd"
ROAD_XSD = f"{ASAM_OPENDRIVE_SCHEMA_DIR}/OpenDRIVE_Road.xsd"

OSI_NAMING_ADOC = (
    "submodules/asam-openx-standards/submodules/open-simulation-interface"
    "/doc/architecture/trace_file_naming.adoc"
)

# Which document deprecates a value. The pinned XSD and the v1.9.0 prose disagree, so the
# distinction is recorded rather than flattened into one set.
XSD = "ASAM OpenDRIVE V1.9.0 XSD <xs:documentation>deprecated</xs:documentation>"
SPEC_11_8 = "ASAM OpenDRIVE v1.9.0 specification §11.8"


# =============================================================================
# Source readers
# =============================================================================


@lru_cache(maxsize=None)
def _xsd_enums(rel_path: str) -> Dict[str, object]:
    """Enumerations of one XSD, via the shared extractor.

    Deliberately not re-implemented here. ``omb.utils.xsd_enum_extractor`` already parses
    both XSD enum shapes and, importantly, recognises ASAM's two ways of marking
    deprecation: a documentation string starting with "deprecated", and one phrased as
    "use X instead" - which is how V1.9.0 marks ``sidewalk``, ``bus``, ``taxi``, ``patch``,
    ``railing``, ``soundBarrier`` and ``streetLamp``. A parser that greps for the word
    "deprecated" alone silently undercounts by seven values.
    """
    return extract_enums_from_dir(_require_schema_dir())


def _xsd_enumeration(
    rel_path: str, type_name: str
) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """Return ``(values, deprecated)`` of an XSD ``simpleType`` enumeration."""
    enums = _xsd_enums(rel_path)
    enum = enums.get(type_name)
    if enum is None:
        raise AssertionError(f"simpleType {type_name!r} not found in {rel_path}")
    return frozenset(enum.value_strings), frozenset(enum.deprecated_values)


def _require_pinned_sources(path: Path, what: str) -> Path:
    """Return *path*, or skip locally / fail where the sources are guaranteed.

    The pinned ASAM schemas and specifications live in a submodule, so a missing checkout
    is a legitimate local state and skipping is right there. In the ``Pinned Standards
    Drift`` job, which initialises the submodule and sets ``OMB_REQUIRE_PINNED_SOURCES=1``,
    a missing file must fail instead: a drift guard that quietly stops running is worse
    than no guard.
    """
    if path.exists():
        return path
    if os.environ.get("OMB_REQUIRE_PINNED_SOURCES"):
        raise AssertionError(
            f"{what} is missing while OMB_REQUIRE_PINNED_SOURCES is set. "
            f"{ASAM_SUBMODULE_HINT}"
        )
    pytest.skip(f"{what} not checked out. {ASAM_SUBMODULE_HINT}")


def _require_schema_dir() -> Path:
    """The pinned OpenDRIVE XSD directory, or skip/fail per the rule above."""
    return _require_pinned_sources(
        Path(ASAM_OPENDRIVE_SCHEMA_DIR), "the pinned ASAM OpenDRIVE schema directory"
    )


def _require_osi_specification() -> Path:
    """Locate the pinned OSI naming conventions, or fail where they are guaranteed.

    The file lives in a nested submodule, so a missing checkout is a legitimate local
    state and skipping is the right answer there. Where the sources *are* guaranteed —
    the ``Pinned Standards Drift`` job, which initialises the submodule and sets
    ``OMB_REQUIRE_PINNED_SOURCES=1`` — a missing file must fail instead: a drift guard
    that quietly stops running is worse than no guard.
    """
    return _require_pinned_sources(ROOT / OSI_NAMING_ADOC, OSI_NAMING_ADOC)


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


# ASAM OpenDRIVE V1.9.0 deprecation state. The schema marks eight lane types; the v1.9.0
# specification §11.8 deprecates one more that the schema does not, so the source is
# recorded per value rather than derived from either document alone.
LANE_DEPRECATED = {
    "sidewalk": XSD,  # use walking
    "bus": XSD,  # use the lane <access> element
    "taxi": XSD,  # use the lane <access> element
    "mwyEntry": XSD,  # use entry
    "mwyExit": XSD,  # use exit
    "special1": XSD,
    "special2": XSD,
    "special3": XSD,
    "bidirectional": SPEC_11_8,  # use the lane @direction attribute
}

OBJECT_DEPRECATED = {
    value: XSD
    for value in (
        # deprecated with a stated replacement
        "patch",  # use roadSurface
        "railing",  # use barrier
        "soundBarrier",  # use barrier
        "streetLamp",  # use pole
        "wind",  # use pole
        # deprecated without a stated replacement
        "car",
        "bus",
        "trailer",
        "bike",
        "motorbike",
        "tram",
        "train",
        "pedestrian",
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


#: (domain, mappings, pinned source). ``scenario`` reads the OpenSCENARIO XML schema
#: rather than the OpenDRIVE directory, and its ``entityTypes`` models the union of three
#: enumerations - see the union handling in ``xsd_shacl_sync.compare_enums``.
SYNC_TARGETS = (
    ("hdmap", HDMAP_ENUM_MAPPINGS, ASAM_OPENDRIVE_SCHEMA_DIR),
    ("ositrace", OSITRACE_ENUM_MAPPINGS, ASAM_OPENDRIVE_SCHEMA_DIR),
    ("scenario", SCENARIO_ENUM_MAPPINGS, ASAM_OPENSCENARIO_SCHEMA_FILE),
)


@pytest.mark.parametrize(
    "domain,mappings,source", SYNC_TARGETS, ids=[t[0] for t in SYNC_TARGETS]
)
def test_enums_match_their_pinned_source(domain, mappings, source):
    """Every mapped ``sh:in`` equals its pinned ASAM enumeration, extensions aside.

    Delegated to ``omb.utils.xsd_shacl_sync.run_sync_check`` rather than reimplemented:
    that module owns the XSD-to-SHACL comparison, including declared extensions such as
    ``truck``. This test is what makes it fail a build instead of only printing a report.
    """
    report = run_sync_check(
        _require_pinned_sources(Path(source), f"the pinned ASAM schema at {source}"),
        Path("artifacts") / domain / f"{domain}.shacl.ttl",
        mappings=mappings,
    )
    assert report.results, f"no mappings checked for {domain}"
    assert report.all_in_sync, "\n".join(
        ["enumeration drift against the pinned ASAM schemas:"]
        + [r.summary() for r in report.results]
        + [
            f"  {r.shacl_property}: missing={sorted(r.missing_in_shacl)} "
            f"undeclared_extra={sorted(r.undeclared_extras)}"
            for r in report.results
            if not r.in_sync
        ]
    )


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda c: c.id)
def test_declared_extensions_match_the_sync_mappings(contract: Contract):
    """The extensions declared here and in the sync mappings cannot drift apart."""
    mappings = (
        HDMAP_ENUM_MAPPINGS if contract.domain == "hdmap" else OSITRACE_ENUM_MAPPINGS
    )
    prop = contract.path[-1]
    declared_in_mapping = {
        e
        for m in mappings
        if m["shacl_property"] == prop
        for e in m.get("extensions", ())
    }
    assert declared_in_mapping == frozenset(contract.extensions), (
        f"{contract.id}: extensions declared in xsd_shacl_sync "
        f"({sorted(declared_in_mapping)}) differ from this contract "
        f"({sorted(contract.extensions)})"
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
