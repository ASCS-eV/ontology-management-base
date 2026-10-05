#!/usr/bin/env python3
"""Tests for omb.api — the supported surface for consuming repositories."""

import contextlib
import io
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from omb.api import check_negative_fixtures, validate_data
from omb.core.result import ReturnCodes, ValidationResult

GX_VALID_DIR = Path("tests/data/gx/valid")
OPENLABEL_INVALID_DIR = Path("tests/data/openlabel-v2/invalid")


def test_validate_data_valid_fixture_dir_returns_success():
    """A known-valid non-vacuous fixture directory should validate successfully."""
    result = validate_data([GX_VALID_DIR])

    assert result.conforms is True
    assert result.return_code == 0
    assert len(result.files_validated) >= 1


def test_validate_data_missing_paths_returns_error_result():
    """Missing paths should return a failed result instead of raising."""
    result = validate_data(["does/not/exist"])

    assert result.conforms is False
    assert result.return_code != 0
    assert result.errors


def test_validate_data_per_resource_returns_aggregated_result():
    """Per-resource validation should aggregate to one ValidationResult."""
    result = validate_data([GX_VALID_DIR], per_resource=True)

    assert isinstance(result, ValidationResult)
    assert len(result.files_validated) >= 1


# =============================================================================
# Vacuous validation: a run that checked nothing must not look like a pass
# =============================================================================


@pytest.fixture
def widget_repo(tmp_path) -> Path:
    """A miniature consuming repository: its own artifacts, valid and invalid data.

    Stands in for a repository that generates artifacts from LinkML and wants to know
    its model still accepts what it should and rejects what it should not.
    """
    artifacts = tmp_path / "artifacts" / "widget"
    artifacts.mkdir(parents=True)
    (artifacts / "widget.owl.ttl").write_text(
        textwrap.dedent("""
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix widget: <https://example.org/widget/v1/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        widget: a owl:Ontology .
        widget:Widget a owl:Class ; rdfs:label "Widget"@en .
        widget:serialNumber a owl:DatatypeProperty ;
            rdfs:domain widget:Widget ; rdfs:range xsd:string .
        """).strip(),
        encoding="utf-8",
    )
    (artifacts / "widget.shacl.ttl").write_text(
        textwrap.dedent("""
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix widget: <https://example.org/widget/v1/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        widget:WidgetShape a sh:NodeShape ;
            sh:targetClass widget:Widget ;
            sh:property [ sh:path widget:serialNumber ;
                sh:datatype xsd:string ;
                sh:minCount 1 ;
                sh:message "Widget requires a serialNumber" ] .
        """).strip(),
        encoding="utf-8",
    )
    (artifacts / "widget.context.jsonld").write_text(
        json.dumps(
            {"@context": {"@vocab": "https://example.org/widget/v1/"}}, indent=2
        ),
        encoding="utf-8",
    )

    context = {"@vocab": "https://example.org/widget/v1/"}
    valid = tmp_path / "data" / "valid"
    valid.mkdir(parents=True)
    (valid / "widget_ok.json").write_text(
        json.dumps(
            {
                "@context": context,
                "@id": "https://example.org/data/widget-1",
                "@type": "Widget",
                "serialNumber": "SN-0001",
            }
        ),
        encoding="utf-8",
    )

    invalid = tmp_path / "data" / "invalid"
    invalid.mkdir(parents=True)
    (invalid / "fail01_missing_serial.json").write_text(
        json.dumps(
            {
                "@context": context,
                "@id": "https://example.org/data/widget-broken",
                "@type": "Widget",
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_validate_data_without_artifacts_does_not_pass_vacuously(widget_repo):
    """Data whose types have no shapes must fail, not report a silent success.

    Forgetting `artifacts=[...]` leaves the validator with an empty shapes graph, and
    pyshacl calls an empty shapes graph conformant — so this used to return
    conforms=True for data that violates its own model.
    """
    result = validate_data([widget_repo / "data" / "valid" / "widget_ok.json"])

    assert result.conforms is False
    assert result.return_code == ReturnCodes.CONFORMANCE_ERROR
    assert result.shapes_loaded == 0
    assert result.types_unrouted == ["https://example.org/widget/v1/Widget"]


def test_empty_shapes_graph_fails_even_without_strict(widget_repo):
    """Zero shapes loaded is a failure in its own right, not a strictness preference.

    `--strict` is off by default in the CLI (the repository's own data has an
    unresolved `did:web:` reference), so the vacuity guard cannot depend on it: a run
    that loaded no shapes expressed no verdict and must not report one.
    """
    result = validate_data(
        [widget_repo / "data" / "valid" / "widget_ok.json"], strict=False
    )

    assert result.conforms is False
    assert result.shapes_loaded == 0
    assert "no shacl shapes were loaded" in result.report_text.lower()


def test_validate_data_with_artifacts_validates_against_the_shapes(widget_repo):
    """With the artifacts registered, valid data passes and shapes are actually loaded."""
    result = validate_data(
        [widget_repo / "data" / "valid" / "widget_ok.json"],
        artifacts=[widget_repo / "artifacts"],
    )

    assert result.conforms is True
    assert result.shapes_loaded >= 1


def test_validate_data_catches_real_violation(widget_repo):
    """A file that violates the model fails when its shapes are available."""
    result = validate_data(
        [widget_repo / "data" / "invalid" / "fail01_missing_serial.json"],
        artifacts=[widget_repo / "artifacts"],
    )

    assert result.conforms is False
    assert result.return_code == ReturnCodes.CONFORMANCE_ERROR


# =============================================================================
# Negative fixtures
# =============================================================================


def test_validate_data_refuses_to_pass_a_negative_fixture_only_set():
    """Negative fixtures are not conformance-checked — and that is not a pass.

    They were silently dropped, so a directory of nothing but negative fixtures
    returned conforms=True with an empty files_validated: a consuming repository
    asserting on .conforms was told its data was fine by a run that checked none of it.
    """
    result = validate_data([OPENLABEL_INVALID_DIR])

    assert result.conforms is False
    assert result.return_code == ReturnCodes.SKIPPED
    assert any("negative fixture" in w.lower() for w in result.warnings)


def test_check_negative_fixtures_accepts_recorded_failures():
    """The repository's own negative fixtures still fail in the recorded way."""
    report = check_negative_fixtures([OPENLABEL_INVALID_DIR])

    assert report.ok, "\n".join(o.message for o in report.failures)
    assert len(report.outcomes) >= 1
    assert all(o.return_code == ReturnCodes.CONFORMANCE_ERROR for o in report.outcomes)
    assert report.return_code == ReturnCodes.SUCCESS


def test_check_negative_fixtures_reports_when_there_are_none(tmp_path):
    """Finding no fixture is an error, not a silent success."""
    (tmp_path / "note.txt").write_text("not data", encoding="utf-8")

    report = check_negative_fixtures([tmp_path])

    assert report.ok is False
    assert report.errors
    assert report.return_code != ReturnCodes.SUCCESS


def test_check_negative_fixtures_records_a_first_snapshot(widget_repo):
    """update=True bootstraps a fixture that has no snapshot yet.

    The pairing rule asks for the snapshot this run is about to write, so recording a
    *first* snapshot was impossible: the file was not yet a fixture, nothing was
    examined, and the run reported success having written nothing.
    """
    data_path = widget_repo / "data" / "invalid" / "fail01_missing_serial.json"
    snapshot = data_path.with_suffix(".expected")
    assert not snapshot.exists()

    report = check_negative_fixtures(
        [data_path], artifacts=[widget_repo / "artifacts"], update=True
    )

    assert report.ok, report.errors
    assert snapshot.is_file()
    assert "Widget requires a serialNumber" in snapshot.read_text(encoding="utf-8")
    assert report.outcomes[0].recorded is True

    # And the recorded snapshot is what a plain (non-update) run then verifies.
    verify = check_negative_fixtures([data_path], artifacts=[widget_repo / "artifacts"])
    assert verify.ok, "\n".join(o.message for o in verify.failures)


def test_check_negative_fixtures_refuses_to_record_a_vacuous_failure(widget_repo):
    """Without shapes a fixture "fails" for the wrong reason; recording that is worse.

    The snapshot would pin the misconfiguration, and the fixture would pass forever
    without a shape ever looking at the data.
    """
    data_path = widget_repo / "data" / "invalid" / "fail01_missing_serial.json"

    report = check_negative_fixtures([data_path], update=True)  # no artifacts

    assert report.ok is False
    assert "refusing to record" in report.failures[0].message.lower()
    assert not data_path.with_suffix(".expected").exists()


def test_check_negative_fixtures_flags_a_fixture_that_stopped_failing(widget_repo):
    """A fixture whose data no longer violates anything is reported, not accepted."""
    data_path = widget_repo / "data" / "invalid" / "fail01_missing_serial.json"
    data_path.with_suffix(".expected").write_text("recorded report", encoding="utf-8")
    # Repair the data so it now conforms.
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    payload["serialNumber"] = "SN-0002"
    data_path.write_text(json.dumps(payload), encoding="utf-8")

    report = check_negative_fixtures([data_path], artifacts=[widget_repo / "artifacts"])

    assert report.ok is False
    assert "expected to fail" in report.failures[0].message


def test_check_negative_fixtures_flags_a_changed_report(widget_repo):
    """A fixture that fails differently than recorded is reported with a diff."""
    data_path = widget_repo / "data" / "invalid" / "fail01_missing_serial.json"
    data_path.with_suffix(".expected").write_text(
        "a report that does not match", encoding="utf-8"
    )

    report = check_negative_fixtures([data_path], artifacts=[widget_repo / "artifacts"])

    assert report.ok is False
    assert report.failures[0].diff


# =============================================================================
# Library hygiene: importing and calling omb must not disturb the host
# =============================================================================


def test_validate_data_produces_no_stdout_or_stderr():
    """validate_data() should be pure with respect to stdout and stderr."""
    out = io.StringIO()
    err = io.StringIO()

    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        result = validate_data([GX_VALID_DIR])

    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert len(result.files_validated) >= 1


def test_api_writes_nothing_to_the_process_streams(widget_repo):
    """Nothing reaches the real stdout/stderr — checked in a separate process.

    contextlib.redirect_stderr cannot see this on its own: a logging StreamHandler
    holds the stderr object it was given when logging was configured, so records kept
    reaching the terminal while an in-process test read an empty buffer. The API used
    to configure that handler simply by being imported.
    """
    script = textwrap.dedent(f"""
        from omb.api import validate_data
        result = validate_data([r"{widget_repo / "data" / "valid"}"])
        assert result.conforms is False, "expected the vacuous-validation failure"
    """)

    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_import_does_not_reconfigure_host_logging():
    """Importing the API must leave the host application's logging setup alone."""
    script = textwrap.dedent("""
        import io, logging, sys
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        import omb.api  # noqa: F401

        logging.getLogger("host.app").info("still mine")
        assert handler in logging.getLogger().handlers, "host handler was removed"
        assert "still mine" in stream.getvalue(), "host log record was diverted"
    """)

    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )

    assert proc.returncode == 0, proc.stderr
