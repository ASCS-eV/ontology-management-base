#!/usr/bin/env python3
"""Pure, side-effect-free validation API for OMB.

FEATURE SET:
============
1. validate_data - Validate JSON-LD data paths and return a ValidationResult
2. ValidationSession - Reuse parsed schemas across many validate() calls
3. check_negative_fixtures - Verify data that must fail against its .expected snapshot
4. FixtureOutcome / FixtureReport - Result types for the negative-fixture flow

USAGE:
======
    from omb.api import check_negative_fixtures, validate_data

    result = validate_data(["tests/data/gx/valid"], artifacts=["./artifacts"])
    if result.conforms:
        handle_success(result)

    report = check_negative_fixtures(["tests/data/gx/invalid"], artifacts=["./artifacts"])
    assert report.ok, [f.message for f in report.failures]

    # Validating many payloads against the same artifacts: parse the shapes once.
    from omb.api import ValidationSession

    session = ValidationSession(artifacts=["./artifacts"])
    results = [session.validate([payload]) for payload in payloads]

DEPENDENCIES:
=============
- pathlib: For path handling
- omb validators and registry utilities

NOTES:
======
- No printing, no argparse, and no sys.exit. Nothing here writes to stdout or
  stderr, and nothing here reconfigures logging: a caller's logging setup decides
  where OMB's records go (`logging.getLogger("omb")` addresses all of them).
- Callers decide how to render results and which process code to return.
- The two functions split the data the way the validators do: `validate_data` is
  for data that must conform, `check_negative_fixtures` for data that must not.
  A file paired with a `.expected` snapshot belongs to the second — see
  :mod:`omb.core.negative_fixtures` — and `validate_data` refuses to quietly
  return success for a set that contains only those.
- `validate_data` and `ValidationSession.validate` share one implementation, so
  the session cannot drift from the one-shot call: the only difference is that
  the session hands down a schema cache that outlives a single call.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from omb.core.negative_fixtures import (
    collect_negative_fixtures,
    expected_snapshot_path,
    is_negative_fixture,
)
from omb.core.result import ReturnCodes, ValidationResult
from omb.utils.file_collector import discover_data_hierarchy
from omb.utils.print_formatter import normalize_text
from omb.utils.registry_resolver import RegistryResolver
from omb.validators.shacl.validator import SchemaCache, ShaclValidator
from omb.validators.validation_suite import ROOT_DIR

__all__ = [
    "validate_data",
    "ValidationSession",
    "check_negative_fixtures",
    "FixtureOutcome",
    "FixtureReport",
    "ValidationResult",
    "ReturnCodes",
]


@dataclass
class FixtureOutcome:
    """What happened to one negative fixture.

    Attributes:
        data_path: The data file that was validated.
        snapshot_path: Its paired ``.expected`` snapshot.
        ok: True when the fixture behaved as recorded (or was recorded, in update mode).
        recorded: True when this call wrote the snapshot.
        return_code: The validation return code (210 = the expected conformance error).
        message: Human-readable explanation, always set when ``ok`` is False.
        report_text: The formatted validation report for this fixture.
        diff: Unified diff of expected vs actual report, when they differ.
    """

    data_path: Path
    snapshot_path: Path
    ok: bool
    recorded: bool = False
    return_code: int = ReturnCodes.SUCCESS
    message: str = ""
    report_text: str = ""
    diff: str = ""


@dataclass
class FixtureReport:
    """Outcome of a whole negative-fixture run.

    ``ok`` is False when any fixture misbehaved *and* when no fixture was found at
    all: a caller asking "do my negative fixtures still fail correctly?" must not be
    told yes by a run that checked nothing.
    """

    outcomes: List[FixtureOutcome] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when at least one fixture was checked and all of them behaved."""
        return (
            not self.errors and bool(self.outcomes) and all(o.ok for o in self.outcomes)
        )

    @property
    def failures(self) -> List[FixtureOutcome]:
        """The fixtures that did not behave as recorded."""
        return [o for o in self.outcomes if not o.ok]

    @property
    def return_code(self) -> int:
        """A process exit code for callers that want one."""
        return ReturnCodes.SUCCESS if self.ok else ReturnCodes.CONFORMANCE_ERROR


def _validate_data_impl(
    data_paths: Sequence[str | Path],
    *,
    artifacts: Optional[Sequence[str | Path]] = None,
    inference_mode: str = "rdfs",
    strict: bool = True,
    per_resource: bool = False,
    allow_online: bool = False,
    enable_http: bool = False,
    root_dir: Optional[Path] = None,
    schema_cache: Optional[dict] = None,
) -> ValidationResult:
    """Validate JSON-LD/TTL data paths and return a ValidationResult.

    Mirrors the CLI data-paths plus check-data-conformance flow, but performs no
    I/O to stdout/stderr and never calls sys.exit. Validator verbosity is forced
    to False.

    Files paired with a ``.expected`` snapshot are negative fixtures — they are
    *meant* to fail — so they are not conformance-checked here. They are named in
    ``result.warnings``, and if they are the only thing supplied the result is a
    failure rather than a vacuous success: verify them with
    :func:`check_negative_fixtures`.

    Args:
        data_paths: Files or directories of JSON-LD data.
        artifacts: Directories of ``{domain}/{domain}.owl.ttl`` (+ shapes, context)
            to register, for types OMB does not ship. Without these, data using your
            own vocabulary has no shapes to validate against.
        inference_mode: ``rdfs`` (default), ``owlrl``, ``none`` or ``both``.
        strict: Unresolved IRIs fail validation. On by default here, unlike the CLI.
        per_resource: Validate each file in its own graph.
        allow_online: Allow HTTP resolution of unresolved IRIs.
        enable_http: Bootstrap OMB's own artifacts over HTTP when absent locally.
        root_dir: Override the root of OMB's built-in data.

    Returns:
        A ValidationResult. ``conforms`` is True only when something was actually
        validated against at least one shape.
    """
    active_root = root_dir or ROOT_DIR
    valid_paths = [Path(path) for path in data_paths if Path(path).exists()]

    if not valid_paths:
        return _error_result("No valid paths provided")
    missing = [str(path) for path in data_paths if not Path(path).exists()]
    if missing:
        return _error_result("Data paths do not exist: " + ", ".join(missing))

    top_level_files, iri_to_file, metadata = discover_data_hierarchy(
        valid_paths, include_did_documents=True
    )
    duplicate_warnings = _duplicate_warnings(metadata.get("duplicate_ids", []))

    # Every requested document is input, regardless of its identifier scheme.
    # Siblings discovered only for reference resolution are not promoted to inputs.
    negative_fixtures = collect_negative_fixtures(valid_paths)
    fixture_warnings = [
        f"Skipped negative fixture (verify with check_negative_fixtures): "
        f"{fixture.name} ←→ {expected_snapshot_path(fixture).name}"
        for fixture in negative_fixtures
    ]
    conformance_files = [
        Path(f) for f in top_level_files if not is_negative_fixture(Path(f))
    ]

    if not conformance_files:
        if negative_fixtures:
            result = _error_result(
                f"Nothing to conformance-check: all {len(negative_fixtures)} supplied "
                f"file(s) are negative fixtures, which are expected to fail. Verify "
                f"them with check_negative_fixtures()."
            )
            result.return_code = ReturnCodes.SKIPPED
        else:
            result = _error_result("No JSON-LD data files found to validate.")
        result.warnings.extend(duplicate_warnings + fixture_warnings)
        return result

    resolver = _build_resolver(active_root, enable_http, iri_to_file, artifacts)

    domain_files = list(conformance_files)
    temp_domain = resolver.create_temporary_domain(domain_files)

    if not temp_domain:
        result = _error_result("Failed to create temporary domain")
        result.warnings.extend(duplicate_warnings + fixture_warnings)
        return result

    validator = ShaclValidator(
        active_root,
        inference_mode=inference_mode,
        verbose=False,
        resolver=resolver,
        strict=strict,
        allow_online=allow_online,
        schema_cache=schema_cache,
    )

    try:
        if per_resource:
            files = [
                Path(file_path)
                for file_path in resolver.get_test_files(temp_domain, test_type="valid")
            ]
            result = _aggregate_results(validator, validator.validate_each(files))
        else:
            result = validator.validate_from_catalog(temp_domain, test_type="valid")
    except (RuntimeError, ValueError) as error:
        result = _error_result(str(error))

    result.warnings.extend(duplicate_warnings + fixture_warnings)
    return result


def validate_data(
    data_paths: Sequence[str | Path],
    *,
    artifacts: Optional[Sequence[str | Path]] = None,
    inference_mode: str = "rdfs",
    strict: bool = True,
    per_resource: bool = False,
    allow_online: bool = False,
    enable_http: bool = False,
    root_dir: Optional[Path] = None,
) -> ValidationResult:
    """Validate JSON-LD/TTL data paths and return a ValidationResult.

    One-shot entry point: every call builds a fresh resolver, registers the
    artifacts and parses the shapes. That is the right trade-off for a single
    validation, but it makes repeated calls pay the same multi-second schema
    setup over and over. Callers validating many payloads against the SAME
    artifacts should use :class:`ValidationSession` instead, which keeps the
    parsed shapes alive between calls.

    Args:
        data_paths: Files or directories containing JSON-LD/TTL to validate.
            Non-existent paths are skipped; an empty effective set is an error.
        artifacts: Extra artifact directories to register, so shapes and
            ontologies outside this repository can be resolved.
        inference_mode: ``rdfs`` (default), ``owlrl``, ``both`` or ``none``.
        strict: If True (default), unresolved IRIs or types fail validation
            instead of only warning.
        per_resource: Validate each file against its own shape subset rather
            than merging everything into one graph. Slower, but pinpoints which
            file a violation came from.
        allow_online: Permit HTTP resolution of IRIs missing from the catalogs.
        enable_http: Bootstrap the catalogs over HTTP when none are local.
        root_dir: Repository root; defaults to the installed OMB root.

    Returns:
        ValidationResult: Conformance flag plus violations, errors and warnings.
    """
    return _validate_data_impl(
        data_paths,
        artifacts=artifacts,
        inference_mode=inference_mode,
        strict=strict,
        per_resource=per_resource,
        allow_online=allow_online,
        enable_http=enable_http,
        root_dir=root_dir,
    )


class ValidationSession:
    """Reusable validation context that parses the shapes only once.

    :func:`validate_data` is stateless, so a caller validating N payloads pays
    the schema discovery, parsing and RDFS-inference cost N times even though
    that work depends only on the artifacts — not on the data. A session hoists
    that cost out of the loop, which is the difference between a per-call and a
    one-off setup for batch validators, API servers and test suites.

    Correctness is preserved by sharing exactly one thing — the parsed schema
    graphs — and nothing else:

    * A FRESH resolver is built per call, so fixture mappings registered while
      validating one payload can never resolve an IRI in the next one. Building
      it is cheap; parsing the shapes is not.
    * Schema DISCOVERY also runs per call, against that fresh resolver. Only the
      parse of the files it resolved is reused, so which shapes apply to a
      payload is decided by the payload, never by a previous one.
    * Entries are keyed by the resolved schema FILES — path, size and
      modification time — plus ``inference_mode``. Payloads needing different
      vocabularies therefore get different entries, payloads needing the same
      ones share a single entry whatever properties they happen to use, and a
      schema edited on disk is reloaded instead of served stale.
    * Cached graphs are treated as read-only, and the single in-place write that
      pyshacl performs on a shapes graph is fixed and idempotent, so it settles
      on first use instead of accumulating.
    * ``artifacts`` and ``root_dir`` are resolved to absolute paths in the
      constructor, so a relative path cannot be re-resolved against a changed
      working directory mid-session.

    The session is therefore equivalent to calling :func:`validate_data`
    repeatedly, and ``tests/test_api.py`` asserts exactly that, including for
    alternating valid/invalid input.

    Not thread-safe: use one session per thread, or guard calls with a lock.

    Usage:
        session = ValidationSession(artifacts=["./artifacts"])
        for payload in payloads:
            result = session.validate([payload])
            print(result.conforms)
    """

    #: Default ceiling on distinct cached schema sets. Each entry holds fully
    #: parsed graphs, and a service validating untrusted documents can meet a new
    #: set for every unrecognised vocabulary, so the cache needs a bound rather
    #: than only a manual :meth:`clear_cache`.
    DEFAULT_MAX_CACHED_SCHEMAS = SchemaCache.DEFAULT_MAX_ENTRIES

    def __init__(
        self,
        *,
        artifacts: Optional[Sequence[str | Path]] = None,
        inference_mode: str = "rdfs",
        strict: bool = True,
        allow_online: bool = False,
        enable_http: bool = False,
        root_dir: Optional[Path] = None,
        max_cached_schemas: int = DEFAULT_MAX_CACHED_SCHEMAS,
    ) -> None:
        """Configure the session. See :func:`validate_data` for the arguments.

        Everything that influences WHICH schemas are loaded is fixed here rather
        than per call, so that one session means one configuration. Only the
        data — and ``per_resource``, which changes how the data is partitioned,
        not which shapes apply — varies per :meth:`validate` call.

        Paths are resolved immediately so that the configuration really is
        fixed: a relative ``artifacts`` entry would otherwise be re-resolved
        against the current working directory on every call, so a session whose
        process chdir'd would start validating against a different directory.

        Args:
            max_cached_schemas: Maximum number of distinct schema sets to keep
                parsed. The least recently used is dropped beyond this. Must be
                at least 1.
        """
        if max_cached_schemas < 1:
            raise ValueError(
                f"max_cached_schemas must be >= 1, got {max_cached_schemas}"
            )
        self._artifacts = (
            [Path(artifact).resolve() for artifact in artifacts]
            if artifacts is not None
            else None
        )
        self._inference_mode = inference_mode
        self._strict = strict
        self._allow_online = allow_online
        self._enable_http = enable_http
        self._root_dir = Path(root_dir).resolve() if root_dir is not None else None
        self._schema_cache = SchemaCache(max_entries=max_cached_schemas)

    def validate(
        self,
        data_paths: Sequence[str | Path],
        *,
        per_resource: bool = False,
    ) -> ValidationResult:
        """Validate ``data_paths`` reusing any schemas already parsed.

        Args:
            data_paths: Files or directories to validate, as in
                :func:`validate_data`.
            per_resource: Validate each file separately instead of merging.

        Returns:
            ValidationResult: Identical to the equivalent
            :func:`validate_data` call.
        """
        return _validate_data_impl(
            data_paths,
            artifacts=self._artifacts,
            inference_mode=self._inference_mode,
            strict=self._strict,
            per_resource=per_resource,
            allow_online=self._allow_online,
            enable_http=self._enable_http,
            root_dir=self._root_dir,
            schema_cache=self._schema_cache,
        )

    def clear_cache(self) -> None:
        """Release the parsed schemas, so the next call reloads what it needs.

        Not required to pick up edited artifacts: entries are keyed by the size
        and modification time of the files they were parsed from, so a changed
        schema is reloaded on its own. Use this to free the memory, or to force
        a reload after a change too subtle for that key to see.
        """
        self._schema_cache.clear()


def check_negative_fixtures(
    data_paths: Sequence[str | Path],
    *,
    artifacts: Optional[Sequence[str | Path]] = None,
    inference_mode: str = "rdfs",
    update: bool = False,
    allow_online: bool = False,
    allow_warnings: bool = True,
    enable_http: bool = False,
    root_dir: Optional[Path] = None,
) -> FixtureReport:
    """Verify that data which must fail still fails in the recorded way.

    The library counterpart of ``--run check-failing-tests``. Same rule: a data file
    is a negative fixture when a ``.expected`` snapshot sits beside it, sharing its
    stem (see :mod:`omb.core.negative_fixtures`). Each one is validated on its own
    and its report compared to the snapshot, so a model change that stops producing a
    violation, or produces a different one, is caught.

    This is what a repository generating artifacts from LinkML wires into its test
    suite::

        report = check_negative_fixtures(["tests/data/invalid"], artifacts=["artifacts"])
        assert report.ok, "\\n".join(f.message for f in report.failures)

    Args:
        data_paths: Files or directories holding negative fixtures. Directories are
            scanned; files without a paired snapshot are ignored unless ``update``.
        artifacts: Artifact directories to register (see :func:`validate_data`).
        inference_mode: ``rdfs`` (default), ``owlrl``, ``none`` or ``both``.
        update: Record each snapshot from the live report instead of comparing.
            Files that have no snapshot yet are recorded when they fail — this is how
            a fixture is bootstrapped — and reported as "not a negative fixture" when
            they pass. Review the diff before committing recorded snapshots.
        allow_online: Allow HTTP resolution of unresolved IRIs.
        allow_warnings: Keep ``sh:Warning``/``sh:Info`` advisory, so a fixture must
            produce a real violation. Advisory results never enter a snapshot.
        enable_http: Bootstrap OMB's own artifacts over HTTP when absent locally.
        root_dir: Override the root of OMB's built-in data.

    Returns:
        A :class:`FixtureReport`. ``report.ok`` is False if any fixture misbehaved or
        if no fixture was found at all.
    """
    active_root = root_dir or ROOT_DIR
    report = FixtureReport()

    valid_paths = [Path(path) for path in data_paths if Path(path).exists()]
    if not valid_paths:
        report.errors.append("No valid paths provided")
        return report

    missing = [str(path) for path in data_paths if not Path(path).exists()]
    if missing:
        report.errors.append("Data paths do not exist: " + ", ".join(missing))
        return report

    candidates = collect_negative_fixtures(valid_paths, include_unpaired=update)
    if not candidates:
        report.errors.append(
            "No negative fixtures found. A data file counts as one when a .expected "
            "snapshot sits beside it (same stem, .expected suffix); pass update=True "
            "to record snapshots for files that fail."
        )
        return report

    _, iri_to_file, _ = discover_data_hierarchy(valid_paths, include_did_documents=True)
    resolver = _build_resolver(active_root, enable_http, iri_to_file, artifacts)

    validator = ShaclValidator(
        active_root,
        inference_mode=inference_mode,
        verbose=False,
        resolver=resolver,
        allow_online=allow_online,
        allow_warnings=allow_warnings,
    )

    for data_path in candidates:
        report.outcomes.append(_check_one_fixture(validator, data_path, update=update))

    if update and not any(outcome.recorded for outcome in report.outcomes):
        report.errors.append("No negative fixture snapshots were recorded.")
    return report


def _check_one_fixture(
    validator: ShaclValidator, data_path: Path, *, update: bool
) -> FixtureOutcome:
    """Validate one fixture and compare (or record) its snapshot."""
    import difflib

    from omb.core.negative_fixtures import snapshot_files_field

    snapshot_path = expected_snapshot_path(data_path)
    recording_new = update and not snapshot_path.is_file()

    try:
        result = validator.validate([data_path])
    except (RuntimeError, ValueError, OSError) as error:
        return FixtureOutcome(
            data_path=data_path,
            snapshot_path=snapshot_path,
            ok=False,
            return_code=ReturnCodes.GENERAL_ERROR,
            message=str(error),
        )
    # Reduced to bare filenames so the snapshot stays independent of where the pair
    # lives; see omb.core.negative_fixtures.snapshot_files_field.
    snapshot_result = dataclasses.replace(
        result, files_validated=snapshot_files_field(result.files_validated)
    )
    report_text = validator.format_result(snapshot_result)

    if result.return_code != ReturnCodes.CONFORMANCE_ERROR:
        if recording_new and result.return_code == ReturnCodes.SUCCESS:
            return FixtureOutcome(
                data_path=data_path,
                snapshot_path=snapshot_path,
                ok=True,
                return_code=result.return_code,
                message=(
                    f"{data_path.name} passed validation, so it is not a negative "
                    f"fixture. No snapshot written."
                ),
                report_text=report_text,
            )
        return FixtureOutcome(
            data_path=data_path,
            snapshot_path=snapshot_path,
            ok=False,
            return_code=result.return_code,
            message=(
                f"{data_path.name} is paired with {snapshot_path.name}, so it is "
                f"expected to fail, but validation returned {result.return_code} "
                f"instead of {int(ReturnCodes.CONFORMANCE_ERROR)}. Either the data no "
                f"longer violates anything (delete the snapshot to treat it as "
                f"ordinary data) or the snapshot is stale."
            ),
            report_text=report_text,
        )

    if update:
        if result.report_graph is None:
            # The fixture "failed" only because nothing could check it. Recording that
            # would pin the misconfiguration into the snapshot, and the fixture would
            # then pass forever without a shape ever looking at it.
            return FixtureOutcome(
                data_path=data_path,
                snapshot_path=snapshot_path,
                ok=False,
                return_code=result.return_code,
                message=(
                    f"Refusing to record {snapshot_path.name}: {data_path.name} did not "
                    f"produce a SHACL validation report. {result.report_text}"
                ),
                report_text=report_text,
            )
        # `newline="\n"` keeps snapshots byte-identical across platforms: `write_text`
        # would otherwise translate to `os.linesep`, so a fixture re-recorded on Windows
        # would differ from the same fixture recorded on Linux/macOS even though
        # `normalize_text` compares them as equal.
        snapshot_path.write_text(report_text, encoding="utf-8", newline="\n")
        return FixtureOutcome(
            data_path=data_path,
            snapshot_path=snapshot_path,
            ok=True,
            recorded=True,
            return_code=result.return_code,
            message=f"Recorded {snapshot_path.name}",
            report_text=report_text,
        )

    expected = normalize_text(snapshot_path.read_text(encoding="utf-8").strip())
    actual = normalize_text(report_text)

    if expected == actual:
        return FixtureOutcome(
            data_path=data_path,
            snapshot_path=snapshot_path,
            ok=True,
            return_code=result.return_code,
            message=f"{data_path.name} failed as recorded in {snapshot_path.name}",
            report_text=report_text,
        )

    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=f"{snapshot_path.name} (expected)",
            tofile=f"{data_path.name} (actual)",
            lineterm="",
        )
    )
    return FixtureOutcome(
        data_path=data_path,
        snapshot_path=snapshot_path,
        ok=False,
        return_code=result.return_code,
        message=(
            f"{data_path.name} failed, but not in the way {snapshot_path.name} records"
        ),
        report_text=report_text,
        diff=diff,
    )


def _build_resolver(
    root_dir: Path,
    enable_http: bool,
    iri_to_file: dict,
    artifacts: Optional[Sequence[str | Path]],
) -> RegistryResolver:
    """Build a resolver with discovered fixtures and caller artifacts registered."""
    resolver = RegistryResolver(root_dir, enable_http=enable_http)

    if iri_to_file:
        resolver.register_fixture_mappings(iri_to_file)

    for artifact in artifacts or []:
        artifact_path = Path(artifact).resolve()
        if artifact_path.is_dir():
            resolver.register_artifact_directory(artifact_path)

    return resolver


def _error_result(message: str) -> ValidationResult:
    """Create a general-error ValidationResult without raising or printing."""
    return ValidationResult(
        conforms=False,
        return_code=ReturnCodes.GENERAL_ERROR,
        report_text=message,
        errors=[message],
    )


def _aggregate_results(
    validator: ShaclValidator, results: Sequence[ValidationResult]
) -> ValidationResult:
    """Aggregate per-resource validation results into one ValidationResult."""
    return_code = next(
        (
            result.return_code
            for result in results
            if result.return_code != ReturnCodes.SUCCESS
        ),
        ReturnCodes.SUCCESS,
    )
    failures = [
        result for result in results if result.return_code != ReturnCodes.SUCCESS
    ]

    return ValidationResult(
        conforms=all(result.conforms for result in results),
        return_code=return_code,
        report_text="\n".join(validator.format_result(result) for result in failures),
        files_validated=[
            file_path for result in results for file_path in result.files_validated
        ],
        triples_count=sum(result.triples_count for result in results),
        inferred_count=sum(result.inferred_count for result in results),
        duration_seconds=sum(result.duration_seconds for result in results),
        errors=[error for result in results for error in result.errors],
        violations=sorted(v for result in results for v in result.violations),
        warnings=[warning for result in results for warning in result.warnings],
        shapes_loaded=max((result.shapes_loaded for result in results), default=0),
        target_types=sorted(
            {target_type for result in results for target_type in result.target_types}
        ),
        types_routed=sorted(
            {target_type for result in results for target_type in result.types_routed}
        ),
        types_unrouted=sorted(
            {target_type for result in results for target_type in result.types_unrouted}
        ),
        per_type_shape_count={
            target_type: count
            for result in results
            for target_type, count in result.per_type_shape_count.items()
        },
    )


def _duplicate_warnings(
    duplicate_ids: Sequence[Tuple[str, Sequence[Path]]],
) -> List[str]:
    """Format duplicate ID metadata as warning strings."""
    return [
        f"Duplicate ID {duplicate_id}: {', '.join(file_path.name for file_path in files)}"
        for duplicate_id, files in duplicate_ids
    ]
