"""
Advisory results stay out of ``ValidationResult.violations`` on real domain data.

hdmap's OpenDRIVE revision checks run at ``sh:Warning`` through ``sh:node``: the
top-level result is a warning while the nested ``sh:or``/``sh:and`` results carry
the default severity, Violation. Only the top-level severity decides conformance,
so these valid instances must conform with no violations, their warnings still
reachable from the report graph.
"""

from pathlib import Path

from omb.api import validate_data
from omb.utils.print_formatter import extract_violations

ROOT_DIR = Path(__file__).resolve().parents[2]
ADVISORY_INSTANCES = sorted(
    (ROOT_DIR / "tests" / "data" / "hdmap" / "valid").glob("*_advisory_instance.json")
)


def test_hdmap_advisory_instances_conform_without_violations():
    assert len(ADVISORY_INSTANCES) == 3

    result = validate_data(ADVISORY_INSTANCES)

    assert result.conforms, result.report_text
    assert result.violations == []
    advisory = extract_violations(result.report_graph, advisory=True)
    assert {v.severity for v in advisory} == {"Warning"}
    assert {v.source_shape.rsplit("/", 1)[-1] for v in advisory} == {
        "OpenDriveLaneTypeRevisionShape",
        "OpenDriveRoadTypeRevisionShape",
    }
