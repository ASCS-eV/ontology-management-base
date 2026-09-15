#!/usr/bin/env python3
"""Pure, side-effect-free validation API for OMB.

FEATURE SET:
============
1. validate_data - Validate JSON-LD data paths and return a ValidationResult
2. check_negative_fixtures - Verify data that must fail against its .expected snapshot
3. FixtureOutcome / FixtureReport - Result types for the negative-fixture flow

USAGE:
======
    from omb.api import check_negative_fixtures, validate_data

    result = validate_data(["tests/data/gx/valid"], artifacts=["./artifacts"])
    if result.conforms:
        handle_success(result)

    report = check_negative_fixtures(["tests/data/gx/invalid"], artifacts=["./artifacts"])
    assert report.ok, [f.message for f in report.failures]

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
from omb.validators.shacl.validator import ShaclValidator
from omb.validators.validation_suite import ROOT_DIR

__all__ = [
    "validate_data",
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

    top_level_files, iri_to_file, metadata = discover_data_hierarchy(valid_paths)
    duplicate_warnings = _duplicate_warnings(metadata.get("duplicate_ids", []))

    # Negative fixtures are excluded from conformance checking, exactly as the CLI
    # excludes them — but silently dropping them let a directory of nothing but
    # negative fixtures return conforms=True over an empty file list, which is the
    # one answer that is never true. Name them, and refuse to call it success.
    #
    # Found from the supplied paths rather than from top_level_files: fixtures that
    # cross-reference each other are all "referenced", so the hierarchy can hand back
    # no top-level file at all, and the caller would then get a bare "nothing to
    # validate" instead of being pointed at check_negative_fixtures().
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
            result = _error_result(
                "No top-level files found to validate: every discovered file is "
                "referenced by another, so all of them were taken for fixtures. Name "
                "the file(s) to validate directly, or use per_resource=True to "
                "validate each document on its own."
            )
        result.warnings.extend(duplicate_warnings + fixture_warnings)
        return result

    resolver = _build_resolver(active_root, enable_http, iri_to_file, artifacts)

    domain_files = list(conformance_files)
    if per_resource and iri_to_file:
        existing = {Path(file_path).resolve() for file_path in domain_files}
        fixture_files = sorted(
            {Path(file_path).resolve() for file_path in iri_to_file.values()}
        )
        domain_files += [
            file_path for file_path in fixture_files if file_path not in existing
        ]

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

    candidates = collect_negative_fixtures(valid_paths, include_unpaired=update)
    if not candidates:
        report.errors.append(
            "No negative fixtures found. A data file counts as one when a .expected "
            "snapshot sits beside it (same stem, .expected suffix); pass update=True "
            "to record snapshots for files that fail."
        )
        return report

    _, iri_to_file, _ = discover_data_hierarchy(valid_paths)
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

    return report


def _check_one_fixture(
    validator: ShaclValidator, data_path: Path, *, update: bool
) -> FixtureOutcome:
    """Validate one fixture and compare (or record) its snapshot."""
    import difflib

    from omb.core.negative_fixtures import snapshot_files_field

    snapshot_path = expected_snapshot_path(data_path)
    recording_new = update and not snapshot_path.is_file()

    result = validator.validate([data_path])
    # Reduced to bare filenames so the snapshot stays independent of where the pair
    # lives; see omb.core.negative_fixtures.snapshot_files_field.
    snapshot_result = dataclasses.replace(
        result, files_validated=snapshot_files_field(result.files_validated)
    )
    report_text = validator.format_result(snapshot_result)

    if result.return_code != ReturnCodes.CONFORMANCE_ERROR:
        if recording_new:
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
        if result.shapes_loaded == 0:
            # The fixture "failed" only because nothing could check it. Recording that
            # would pin the misconfiguration into the snapshot, and the fixture would
            # then pass forever without a shape ever looking at it.
            return FixtureOutcome(
                data_path=data_path,
                snapshot_path=snapshot_path,
                ok=False,
                return_code=result.return_code,
                message=(
                    f"Refusing to record {snapshot_path.name}: no SHACL shapes were "
                    f"loaded for {data_path.name}, so its failure says nothing about "
                    f"the data. Register the artifacts that define its types."
                ),
                report_text=report_text,
            )
        snapshot_path.write_text(report_text, encoding="utf-8")
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
