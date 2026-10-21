#!/usr/bin/env python3
"""Tests for omb.api — the supported surface for consuming repositories."""

import contextlib
import io
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from omb.api import ValidationSession, check_negative_fixtures, validate_data
from omb.core.result import ReturnCodes, ValidationResult
from omb.utils.registry_resolver import RegistryResolver
from omb.validators.shacl.validator import SchemaCache, ShaclValidator

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
# ValidationSession: reusing parsed schemas must not change any verdict
# =============================================================================


def _verdict(result):
    """The part of a result a consumer actually branches on."""
    return (
        result.conforms,
        result.return_code,
        result.shapes_loaded,
        sorted(str(v) for v in result.violations),
    )


def test_validation_session_matches_validate_data_for_valid_input(widget_repo):
    """A session must return exactly what the one-shot call returns."""
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    one_shot = validate_data([target], artifacts=artifacts)
    session = ValidationSession(artifacts=artifacts).validate([target])

    assert _verdict(session) == _verdict(one_shot)
    assert session.conforms is True


def test_validation_session_matches_validate_data_for_invalid_input(widget_repo):
    """Caching must not swallow a violation the one-shot call reports."""
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "invalid" / "fail01_missing_serial.json"

    one_shot = validate_data([target], artifacts=artifacts)
    session = ValidationSession(artifacts=artifacts).validate([target])

    assert _verdict(session) == _verdict(one_shot)
    assert session.conforms is False


def test_validation_session_alternating_inputs_do_not_bleed(widget_repo):
    """The decisive test: reuse must not let one validation affect the next.

    pyshacl is handed ``inplace=True``, and the session deliberately shares its parsed
    shapes between calls, so a leak would show up here as a valid file inheriting the
    previous failure (or an invalid file inheriting the previous pass).
    """
    artifacts = [widget_repo / "artifacts"]
    good = widget_repo / "data" / "valid" / "widget_ok.json"
    bad = widget_repo / "data" / "invalid" / "fail01_missing_serial.json"

    session = ValidationSession(artifacts=artifacts)
    observed = [
        session.validate([path]).conforms for path in (good, bad, good, bad, good)
    ]

    assert observed == [True, False, True, False, True]


def test_validation_session_repeated_calls_stay_identical(widget_repo):
    """The same input validated repeatedly must give a byte-identical verdict."""
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    session = ValidationSession(artifacts=artifacts)
    verdicts = [_verdict(session.validate([target])) for _ in range(3)]

    assert verdicts[0] == verdicts[1] == verdicts[2]


def test_validation_session_reuses_cached_schemas(widget_repo):
    """Two calls with the same schema footprint must populate exactly one cache entry.

    This is what makes the session worth having: without it each call reparses the
    shapes. Asserted structurally rather than by timing, which would be flaky.
    """
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    session = ValidationSession(artifacts=artifacts)
    assert session._schema_cache == {}

    session.validate([target])
    assert len(session._schema_cache) == 1

    session.validate([target])
    assert len(session._schema_cache) == 1


def test_validation_session_clear_cache_drops_parsed_schemas(widget_repo):
    """clear_cache() must force the next call to reload, for on-disk artifact changes."""
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    session = ValidationSession(artifacts=artifacts)
    session.validate([target])
    assert session._schema_cache

    session.clear_cache()
    assert session._schema_cache == {}

    assert session.validate([target]).conforms is True


def test_validation_session_per_resource_matches_validate_data(widget_repo):
    """per_resource is a per-call argument and must still match the one-shot call."""
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    one_shot = validate_data([target], artifacts=artifacts, per_resource=True)
    session = ValidationSession(artifacts=artifacts).validate(
        [target], per_resource=True
    )

    assert _verdict(session) == _verdict(one_shot)


def test_validation_session_without_artifacts_does_not_pass_vacuously(widget_repo):
    """The vacuity guard must survive the session path, not just the one-shot path."""
    session = ValidationSession()
    result = session.validate([widget_repo / "data" / "valid" / "widget_ok.json"])

    assert result.conforms is False
    assert result.shapes_loaded == 0


def test_validation_session_cached_graphs_stay_stable(widget_repo):
    """Repeated validation must not grow the cached graphs.

    pyshacl's ShapesGraph writes a small fixed set of system triples into the
    shapes graph it is handed, which is the cached one. That write has to settle
    on first use rather than accumulate, or the session would slowly drift away
    from what a one-shot call validates against.
    """
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    session = ValidationSession(artifacts=artifacts)
    sizes = []
    for _ in range(4):
        session.validate([target])
        entry = next(iter(session._schema_cache.values()))
        sizes.append((len(entry.shacl), len(entry.ontology)))

    assert len(set(sizes)) == 1, f"cached graphs grew across calls: {sizes}"


def test_validation_session_resolves_relative_artifacts_at_construction(
    widget_repo, monkeypatch
):
    """A relative artifacts path must be pinned when the session is built.

    Otherwise it is re-resolved against the CWD on every call, so a process that
    chdir'd mid-session would silently validate against a different directory —
    or against none, while the cache still answered from the old one.
    """
    monkeypatch.chdir(widget_repo)
    session = ValidationSession(artifacts=["artifacts"])

    first = session.validate([widget_repo / "data" / "valid" / "widget_ok.json"])
    assert first.conforms is True

    monkeypatch.chdir(widget_repo.parent)
    second = session.validate([widget_repo / "data" / "valid" / "widget_ok.json"])

    assert _verdict(second) == _verdict(first)


def test_validation_session_separates_cache_entries_by_inference_mode(widget_repo):
    """Two sessions over the same schemas but not the same mode must not collide.

    The cached ontology closure is a real RDFS closure under ``rdfs`` and the raw
    graph otherwise, so the mode belongs in the key.
    """
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    shared = SchemaCache()
    for mode in ("rdfs", "none"):
        session = ValidationSession(artifacts=artifacts, inference_mode=mode)
        session._schema_cache = shared
        session.validate([target])

    assert len(shared) == 2, "inference_mode must not collide in the schema cache"


def test_validation_session_separates_cache_entries_by_artifacts(widget_repo, tmp_path):
    """Two sessions over DIFFERENT artifacts must not answer from each other.

    The artifact directories a session registers decide which files schema
    discovery resolves, and they are not visible as a configuration value inside
    the validator. Keying on the resolved files rather than on the IRIs in the
    data is what makes sharing a cache safe here: a second session pointed at a
    copy of the artifacts whose shapes demand something else must see its own
    shapes, not the first session's.
    """
    stricter = tmp_path / "stricter"
    shutil.copytree(widget_repo / "artifacts", stricter)
    shacl = stricter / "widget" / "widget.shacl.ttl"
    shacl.write_text(
        shacl.read_text(encoding="utf-8").replace(
            'sh:message "Widget requires a serialNumber"',
            'sh:pattern "^NOPE-" ; sh:message "Widget requires a serialNumber"',
        ),
        encoding="utf-8",
    )

    target = widget_repo / "data" / "valid" / "widget_ok.json"
    shared = SchemaCache()

    lenient = ValidationSession(artifacts=[widget_repo / "artifacts"])
    lenient._schema_cache = shared
    strict = ValidationSession(artifacts=[stricter])
    strict._schema_cache = shared

    assert lenient.validate([target]).conforms is True
    assert strict.validate([target]).conforms is False
    assert lenient.validate([target]).conforms is True


def test_validation_session_reloads_a_schema_edited_on_disk(widget_repo):
    """An edited artifact must be picked up without an explicit clear_cache().

    A long-lived session next to a repository that regenerates its artifacts
    would otherwise keep reporting verdicts from the shapes as they were when it
    first read them, with nothing in the result to say so.
    """
    artifacts = [widget_repo / "artifacts"]
    target = widget_repo / "data" / "valid" / "widget_ok.json"

    session = ValidationSession(artifacts=artifacts)
    assert session.validate([target]).conforms is True

    shacl = widget_repo / "artifacts" / "widget" / "widget.shacl.ttl"
    shacl.write_text(
        shacl.read_text(encoding="utf-8").replace(
            'sh:message "Widget requires a serialNumber"',
            'sh:pattern "^NOPE-" ; sh:message "Widget requires a serialNumber"',
        ),
        encoding="utf-8",
    )

    assert session.validate([target]).conforms is False


def test_validation_session_shares_one_entry_across_differing_documents(widget_repo):
    """Documents resolving the same schemas must share a single parsed copy.

    Keying on the IRIs a document happens to use splits the cache by optional
    property: two widgets that differ only in whether they carry a label would
    each parse and retain the whole vocabulary. The files they need are the same,
    so the entry must be too.
    """
    artifacts = [widget_repo / "artifacts"]
    directory = widget_repo / "data" / "variants"
    directory.mkdir(parents=True)
    for index, extra in enumerate(({}, {"label": "a"}, {"label": "b", "note": "c"})):
        (directory / f"widget{index}.json").write_text(
            json.dumps(
                {
                    "@context": {"@vocab": "https://example.org/widget/v1/"},
                    "@id": f"https://example.org/data/widget-{index}",
                    "@type": "Widget",
                    "serialNumber": f"SN-{index}",
                    **extra,
                }
            ),
            encoding="utf-8",
        )

    session = ValidationSession(artifacts=artifacts)
    for document in sorted(directory.glob("*.json")):
        session.validate([document])

    assert len(session._schema_cache) == 1


def test_schema_cache_bounds_a_bare_validator(widget_repo):
    """The bound belongs to the cache, so a direct ShaclValidator gets it too.

    ``ValidationSession`` is not the only way to hand a validator a shared cache,
    and a bound enforced only by the session would leave every other caller with
    an unbounded one.
    """
    resolver = RegistryResolver(widget_repo)
    resolver.register_artifact_directory(widget_repo / "artifacts")
    cache = SchemaCache(max_entries=1)
    validator = ShaclValidator(
        widget_repo, verbose=False, resolver=resolver, schema_cache=cache
    )

    for vocabulary in ("https://example.org/widget/v1/", "https://example.org/other/"):
        validator._load_schemas({f"{vocabulary}Widget"}, set(), set())

    assert len(cache) == 1


def test_schema_cache_rejects_an_unusable_bound():
    """A bound below 1 would cache nothing and silently defeat the cache."""
    with pytest.raises(ValueError, match="max_entries"):
        SchemaCache(max_entries=0)


def test_schema_cache_evicts_least_recently_used(widget_repo):
    """A schema set that keeps being used must not be evicted by one-off ones.

    Insertion order alone would drop the entry a caller relies on every call as
    soon as two unfamiliar documents arrived after it.
    """
    cache = SchemaCache(max_entries=2)
    cache["a"] = 1
    cache["b"] = 2
    assert cache.get("a") == 1

    cache["c"] = 3

    assert sorted(cache) == ["a", "c"], "reads must count as use"


def test_validation_session_bounds_its_cache(widget_repo):
    """The cache must be bounded, not grow once per distinct document type.

    A server validating untrusted documents sees a new schema set for every
    unrecognised vocabulary, so an unbounded cache is a memory leak driven by
    input.
    """
    session = ValidationSession(
        artifacts=[widget_repo / "artifacts"], max_cached_schemas=2
    )
    data_dir = widget_repo / "data" / "footprints"
    data_dir.mkdir(parents=True)

    for index in range(5):
        document = data_dir / f"doc{index}.json"
        document.write_text(
            json.dumps(
                {
                    "@context": {"@vocab": f"https://example.org/unknown{index}/v1/"},
                    "@id": f"https://example.org/data/widget-{index}",
                    "@type": f"Unknown{index}",
                }
            ),
            encoding="utf-8",
        )
        session.validate([document])

    assert len(session._schema_cache) <= 2


def test_validation_session_rejects_an_unusable_cache_bound():
    """A bound below 1 would cache nothing and silently defeat the session."""
    with pytest.raises(ValueError, match="max_cached_schemas"):
        ValidationSession(max_cached_schemas=0)


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
