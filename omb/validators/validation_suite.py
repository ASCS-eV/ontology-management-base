#!/usr/bin/env python3
"""
Validation Suite for Ontology Management Base

This script acts as the central entry point for validating ontology artifacts,
SHACL shapes, and test data. It ensures that changes to the ontology structure
or data definitions comply with defined standards.

PREREQUISITES:
=============
- Python 3.12 or higher
- Catalogs must be generated (run: python -m omb.utils.registry_updater). An installed
  package ships them; only a source checkout regenerates them.
- No virtual environment is required. Working in a checkout without one is only warned
  about, because the dependencies there are probably stale; --skip-env-check silences it.

OPERATION MODES:
===============

1. AUTO DISCOVERY MODE (Default)
   Scans the test catalog (tests/catalog-v001.xml) and validates ALL registered domains.
   Usage:
     python3 -m omb.validators.validation_suite

2. DOMAIN SELECTION MODE
   Restricts catalog-based validation to specific domains.
   Usage:
     python3 -m omb.validators.validation_suite --domain manifest
     python3 -m omb.validators.validation_suite --domain manifest scenario

3. DATA PATHS MODE
   Validates arbitrary files or directories with auto-discovery of fixtures.
   Usage:
     python3 -m omb.validators.validation_suite --data-paths tests/data/manifest/valid/
     python3 -m omb.validators.validation_suite --data-paths ./my_data.json

ADDITIONAL OPTIONS:
==================

--data-paths PATH [PATH ...]
    Files or directories containing JSON-LD data to validate.

    Behavior:
    - FILE: Validates this file. Parent directory is scanned for fixtures.
    - DIRECTORY: Scans recursively. Auto-detects top-level files vs fixtures.

    Top-level files (validated): Files whose @id is NOT referenced by others.
    Fixtures (auto-loaded): Files whose @id IS referenced by top-level files.

    Examples:
      --data-paths ./my-credential.json
      --data-paths ./examples/
      --data-paths ./data/credential.json ./data/did-documents/

--artifacts DIR [DIR ...]
    Register additional artifact directories for schema discovery and context inlining.
    Each directory should follow the standard structure:
      artifacts/{domain}/{domain}.owl.ttl
      artifacts/{domain}/{domain}.shacl.ttl
      artifacts/{domain}/{domain}.context.jsonld

    This enables validation of data that uses schemas from external repositories.
    Example:
      python3 -m omb.validators.validation_suite --data-paths ./my-data.json \\
          --artifacts ../other-repo/artifacts

VALIDATION PHASES (--run):
=========================

--run all (default)
    Executes all applicable checks for the selected mode.

--run check-syntax
    Validates the syntax of RDF artifacts.
    - JSON-LD: Checks for well-formed JSON.
    - Turtle (.ttl): Checks for valid Turtle syntax.

--run check-artifact-coherence
    (Catalog/Domain Mode only)
    Validates that SHACL NodeShapes target classes that actually exist in the OWL ontology.
    Ensures alignment between the shapes and the ontology definitions.

--run check-data-conformance
    Validates JSON-LD data instances against their associated SHACL shapes.
    - In Catalog Mode: Uses shapes linked in the catalog.
    - In Data Path Mode: Discovers schemas from --artifacts directories.

--run check-failing-tests
    Executes "Negative Tests" - data files expected to fail validation.
    Verifies that they fail with the specific error code/message defined in
    .expected files. A data file counts as a negative test when a `.expected`
    snapshot sits beside it, wherever it lives, so this works identically in
    Catalog/Domain Mode and Data Path Mode. Pass --update-expected to (re)record
    each .expected snapshot from the live validation report instead of comparing.

EXAMPLES:
=========
# Run everything on the whole repository
python3 -m omb.validators.validation_suite

# Check only syntax for the 'manifest' domain
python3 -m omb.validators.validation_suite --run check-syntax --domain manifest

# Validate data with auto-discovery of fixtures
python3 -m omb.validators.validation_suite --run check-data-conformance \\
    --data-paths ./examples/

# Validate a single file (parent dir scanned for fixtures)
python3 -m omb.validators.validation_suite --run check-data-conformance \\
    --data-paths ./examples/my-data.json --artifacts ./artifacts
"""

import argparse
import dataclasses
import difflib
import os
import sys
from pathlib import Path
from typing import List

from omb.core.logging import configure_cli_logging
from omb.core.negative_fixtures import (
    expected_snapshot_path,
    snapshot_files_field,
)
from omb.core.paths import builtin_data_root
from omb.core.result import ReturnCodes
from omb.utils.file_collector import discover_data_hierarchy
from omb.utils.print_formatter import (
    ensure_utf8_output,
    normalize_path_for_display,
    normalize_text,
)
from omb.utils.registry_resolver import TEMP_DOMAIN_PREFIX, RegistryResolver
from omb.validators.coherence_validator import validate_artifact_coherence
from omb.validators.shacl.validator import ShaclValidator
from omb.validators.syntax_validator import (
    check_json_wellformedness,
    check_turtle_wellformedness,
)

# Default root for OMB's built-in data. Functions accept root_dir as a
# parameter; this is only the fallback. Single seam: builtin_data_root().
ROOT_DIR = builtin_data_root()

# Known upstream coherence failures that should warn instead of fail.
# Maps (domain, lowercase_class_name) -> upstream issue URL.
# Remove entries once the upstream issue is resolved.
KNOWN_COHERENCE_ISSUES = {
    ("gx", "consent"): (
        "https://gitlab.com/gaia-x/technical-committee/"
        "service-characteristics-working-group/service-characteristics/-/issues/353"
    ),
}


def get_resolver_root_dir(resolver: RegistryResolver | None) -> Path:
    """Return the active repository root for a resolver, falling back to ROOT_DIR."""
    candidate = getattr(resolver, "root_dir", ROOT_DIR) if resolver else ROOT_DIR
    return Path(candidate) if candidate is not None else ROOT_DIR


def check_syntax_all(
    ontology_domains: List[str],
    resolver: RegistryResolver = None,
) -> int:
    """
    Check the syntax of all Turtle (.ttl) and JSON-LD (.json) files.

    All files are discovered via the catalog system. If a resolver with temporary
    entries is provided, those entries are included in the syntax check.

    Args:
        ontology_domains: List of domain names to check (used for filtering)
        resolver: Optional pre-configured RegistryResolver (with temporary entries)

    Returns:
        0 on success, non-zero on failure
    """
    if not ontology_domains:
        return 0

    # Use provided resolver or create new one
    catalog_resolver = resolver if resolver else RegistryResolver(ROOT_DIR)
    root_dir = get_resolver_root_dir(catalog_resolver)

    print("\n=== Checking JSON-LD syntax ===", flush=True)

    # Check if we have data to validate (either from catalog or temporary domains)
    has_temp_domains = any(d.startswith(TEMP_DOMAIN_PREFIX) for d in ontology_domains)
    if not catalog_resolver.is_catalog_loaded() and not has_temp_domains:
        print(
            "❌ Error: No data to validate. Either load catalog or use --data-paths.",
            file=sys.stderr,
        )
        return 1

    # Collect files from catalogs filtered by domain via unified API
    cataloged_files = catalog_resolver.get_all_cataloged_files(
        extensions={".json", ".jsonld", ".ttl"},
        include_artifacts=True,
        domains=ontology_domains,
    )

    # Build file lists from catalog results
    json_files_to_check = [str(p) for p in cataloged_files.get(".json", [])] + [
        str(p) for p in cataloged_files.get(".jsonld", [])
    ]
    ttl_files_to_check = [str(p) for p in cataloged_files.get(".ttl", [])]

    # Check JSON-LD files
    for json_file in sorted(set(json_files_to_check)):
        code, results = check_json_wellformedness(json_file, root_dir)
        for c, msg in results:
            if c != 0:
                print(msg, file=sys.stderr)
                return c
            print(msg)

    print("\n=== Checking TTL syntax ===", flush=True)

    # Check TTL files
    if ttl_files_to_check:
        for ttl_file in sorted(set(ttl_files_to_check)):
            code, results = check_turtle_wellformedness(ttl_file, root_dir)
            for c, msg in results:
                if c != 0:
                    print(msg, file=sys.stderr)
                    return c
                print(msg)
    else:
        print("  No TTL files in catalog to check")

    print("📌 Completed TTL and JSON syntax tests", flush=True)
    return 0


def _report_skipped_domain(
    domain: str, resolver: RegistryResolver, root_dir: Path
) -> None:
    """Explain why conformance validated nothing for ``domain``.

    "No files found" is misleading when files *were* supplied but every one of them is a
    negative fixture: conformance leaves those to ``check-failing-tests``, which compares
    each against its snapshot. Name the pairs so the reason is on the page rather than in
    the reader's head.
    """
    negatives = resolver.get_test_files(domain, test_type="invalid")
    if not negatives:
        print(f"⚠️ No JSON-LD files found in '{domain}'. Skipping.", flush=True)
        return

    print(
        f"⏭️  Nothing to conformance-check in '{domain}': all "
        f"{len(negatives)} file(s) are negative fixtures, verified by "
        f"check-failing-tests against their snapshots.",
        flush=True,
    )
    for path in negatives:
        data_path = Path(path)
        print(
            f"     {normalize_path_for_display(data_path, root_dir)}"
            f"  ←→  {expected_snapshot_path(data_path).name}",
            flush=True,
        )


def validate_data_conformance_all(
    ontology_domains: List[str],
    resolver: RegistryResolver = None,
    inference_mode: str = "rdfs",
    strict: bool = False,
    allow_online: bool = True,
    per_resource: bool = False,
    allow_warnings: bool = True,
) -> int:
    """
    Validate JSON-LD files against SHACL schemas.

    All files are discovered via the catalog system. If a resolver with temporary
    entries is provided, those entries are included in the validation.

    Args:
        ontology_domains: List of domain names to test
        resolver: Optional pre-configured RegistryResolver (with temporary entries)
        inference_mode: Inference mode for SHACL validation (rdfs|owlrl|none|both)
        strict: If True, unresolved IRIs cause validation failure
        allow_online: If True, attempt HTTP resolution for unresolved IRIs
        allow_warnings: If True (default), `sh:Warning`/`sh:Info` results are
            reported as advisory and do not fail the check

    Returns:
        0 on success, non-zero on failure
    """
    if not ontology_domains:
        return 0
    print("\n=== Checking JSON-LD against SHACL ===", flush=True)

    catalog_resolver = resolver if resolver else RegistryResolver(ROOT_DIR)
    root_dir = get_resolver_root_dir(catalog_resolver)

    # Check if we have data to validate (either from catalog or temporary domains)
    has_temp_domains = any(d.startswith(TEMP_DOMAIN_PREFIX) for d in ontology_domains)
    if not catalog_resolver.is_catalog_loaded() and not has_temp_domains:
        print(
            "❌ Error: No data to validate. Either load catalog or use --data-paths.",
            file=sys.stderr,
        )
        return 1

    print("📋 Using catalog-based test discovery\n", flush=True)

    # Create validator with shared resolver
    # Note: enable_http is not passed here because catalog_resolver is already
    # HTTP-bootstrapped when --remote is used.  ShaclValidator uses the
    # pre-built resolver directly.
    validator = ShaclValidator(
        root_dir,
        inference_mode=inference_mode,
        verbose=True,
        resolver=catalog_resolver,
        strict=strict,
        allow_online=allow_online,
        allow_warnings=allow_warnings,
    )

    for domain in ontology_domains:
        print(
            f"\n🔍 Starting JSON-LD SHACL validation for domain: {domain}", flush=True
        )

        # Per-resource mode: validate each file in its own graph (no merging),
        # sharing loaded shapes + ontology closure. Correct for VC/DID documents
        # that legitimately reuse IRIs across files.
        if per_resource:
            from pathlib import Path as _Path

            files = [
                _Path(f)
                for f in validator.resolver.get_test_files(domain, test_type="valid")
            ]
            if not files:
                _report_skipped_domain(domain, validator.resolver, root_dir)
                continue
            print(f"   Found {len(files)} test files from catalog (per-resource)")
            results = validator.validate_each(files)
            domain_failed = False
            for res in results:
                fname = res.files_validated[0] if res.files_validated else "?"
                if res.return_code != 0:
                    domain_failed = True
                    print(f"   ❌ {fname}", flush=True)
                    print(validator.format_result(res), flush=True)
                else:
                    print(f"   ✅ {fname}", flush=True)
            if domain_failed:
                print(
                    f"\n❌ Error during JSON-LD SHACL validation for domain "
                    f"'{domain}'. Aborting.",
                    file=sys.stderr,
                    flush=True,
                )
                return 210
            print(f"\n✅ {domain} conforms to SHACL constraints (per-resource).")
            continue

        # Use catalog-based validation method
        try:
            result = validator.validate_from_catalog(domain, test_type="valid")
        except (RuntimeError, ValueError) as e:
            print(f"\n\u274c {e}", file=sys.stderr, flush=True)
            return 1

        if not result.files_validated:
            _report_skipped_domain(domain, validator.resolver, root_dir)
            continue

        print(f"   Found {len(result.files_validated)} test files from catalog")

        advisory = validator.format_advisory(result)

        if result.return_code != 0:
            print("\n📄 SHACL validation report:", flush=True)
            print(validator.format_result(result), flush=True)
            if advisory:
                print(advisory, flush=True)

            print(
                f"\n❌ Error during JSON-LD SHACL validation for domain '{domain}'. Aborting.",
                file=sys.stderr,
                flush=True,
            )
            return result.return_code
        else:
            if advisory:
                print(advisory, flush=True)
            print(f"\n✅ {domain} conforms to SHACL constraints.", flush=True)

    return 0


def check_failing_tests_all(
    ontology_domains: List[str],
    resolver: RegistryResolver = None,
    inference_mode: str = "rdfs",
    allow_online: bool = True,
    update_expected: bool = False,
    allow_warnings: bool = True,
    require_fixtures: bool = False,
) -> int:
    """
    Run failing test cases from tests/data/{domain}/invalid/ directories.

    All files are discovered via the catalog system. If a resolver with temporary
    entries is provided, those entries are included in the validation.

    Args:
        ontology_domains: List of domain names to test
        resolver: Optional pre-configured RegistryResolver (with temporary entries)
        inference_mode: Inference mode for SHACL validation (rdfs|owlrl|none|both)
        allow_online: If True, attempt HTTP resolution for unresolved IRIs
        update_expected: If True, (re)record each `.expected` snapshot from the
            live validation report instead of comparing against it. A file that has
            no snapshot yet is recorded when it fails, and reported as "not a negative
            fixture" when it passes.
        allow_warnings: If True (default), `sh:Warning`/`sh:Info` results are
            advisory: they are printed after the report but never recorded into
            a `.expected` snapshot, so a negative fixture still has to produce a
            real violation to pass.
        require_fixtures: If True, finding no negative fixture at all is an error
            rather than a silent success. Set when the caller named the files it
            wants checked (data-paths mode with an explicit `--run
            check-failing-tests`), where "nothing to do" means the request was not
            understood, not that there was no work. Left False in domain mode, where
            a domain legitimately has no negative fixtures.

    Returns:
        0 on success, non-zero on failure
    """
    if not ontology_domains:
        return 0
    print("\n=== Running failing tests ===", flush=True)

    catalog_resolver = resolver if resolver else RegistryResolver(ROOT_DIR)
    root_dir = get_resolver_root_dir(catalog_resolver)

    # Check if we have data to validate (either from catalog or temporary domains)
    has_temp_domains = any(d.startswith(TEMP_DOMAIN_PREFIX) for d in ontology_domains)
    if not catalog_resolver.is_catalog_loaded() and not has_temp_domains:
        print(
            "❌ Error: No data to validate. Either load catalog or use --data-paths.",
            file=sys.stderr,
        )
        return 1

    print("📋 Using catalog-based test discovery\n", flush=True)

    # Create validator with shared resolver (already HTTP-bootstrapped if --remote)
    validator = ShaclValidator(
        root_dir,
        inference_mode=inference_mode,
        verbose=True,
        resolver=catalog_resolver,
        allow_online=allow_online,
        allow_warnings=allow_warnings,
    )

    examined = 0

    for domain in ontology_domains:
        print(f"\n🔍 Running failing tests for domain: {domain}", flush=True)

        invalid_test_files = catalog_resolver.get_test_files(
            domain, test_type="invalid"
        )
        if not invalid_test_files:
            continue

        for test_abs_path in invalid_test_files:
            test_abs_path = Path(test_abs_path)
            test_path = normalize_path_for_display(test_abs_path, root_dir)
            expected_output_path = expected_snapshot_path(test_abs_path)
            expected_path_display = normalize_path_for_display(
                expected_output_path, root_dir
            )
            recording_new = update_expected and not expected_output_path.exists()

            if not expected_output_path.exists() and not update_expected:
                print(
                    f"⚠️ No expected output file found: {expected_path_display}",
                    file=sys.stderr,
                    flush=True,
                )
                return 1

            examined += 1

            # Say out loud which snapshot is standing behind this file, so a reader can
            # tell at a glance why a failing validation is about to be accepted.
            if recording_new:
                print(f"🔍 Recording candidate: {test_path}", flush=True)
                print(f"   Snapshot to write: {expected_path_display}", flush=True)
            else:
                print(f"🔍 Negative fixture: {test_path}", flush=True)
                print(f"   Paired snapshot: {expected_path_display}", flush=True)

            # Validate single file (fixtures/schemas resolved via catalog)
            result = validator.validate([test_abs_path])
            # The report about to be printed is also the one written to, or compared
            # against, the `.expected` snapshot below. Its validated-file line is
            # reduced to a bare filename first: the pairing above already establishes
            # location from `test_path`/`expected_path_display`, so a full path here
            # would only tie the snapshot to wherever it happened to be recorded,
            # making the one relocation the pairing rule tolerates - moving a fixture
            # and its snapshot together - report a spurious mismatch. See
            # `snapshot_files_field`.
            snapshot_result = dataclasses.replace(
                result, files_validated=snapshot_files_field(result.files_validated)
            )
            output = validator.format_result(snapshot_result)
            print(output)
            # Advisory results are shown but deliberately excluded from `output`,
            # which is what gets recorded as the `.expected` snapshot.
            advisory = validator.format_advisory(snapshot_result)
            if advisory:
                print(advisory)
            print("\n", flush=True)

            if result.return_code == 210:
                if update_expected and result.report_graph is None:
                    # The fixture "failed" only because nothing could check it.
                    # Recording that pins the misconfiguration into the snapshot, and
                    # the fixture then passes forever without a shape ever looking at
                    # it — the exact failure mode this check exists to prevent.
                    print(
                        f"\n❌ Refusing to record {expected_path_display}: validation "
                        f"did not produce a SHACL report. {result.report_text}",
                        file=sys.stderr,
                        flush=True,
                    )
                    return ReturnCodes.CONFORMANCE_ERROR
                if update_expected:
                    expected_output_path.write_text(output, encoding="utf-8")
                    print(
                        "📝 Recorded expected snapshot: "
                        f"{normalize_path_for_display(expected_output_path, root_dir)}",
                        flush=True,
                    )
                    continue

                expected_output = expected_output_path.read_text(
                    encoding="utf-8"
                ).strip()
                output_norm = normalize_text(output)
                expected_norm = normalize_text(expected_output)

                if output_norm == expected_norm:
                    print(
                        "   Validation returned 210 (conformance error), as recorded",
                        flush=True,
                    )
                    print(
                        f"✅ {test_path} failed as expected: its report matches "
                        f"{expected_path_display}, so the failure is accepted.",
                        flush=True,
                    )
                else:
                    print(
                        f"\n❌ Error: {test_path} failed, but not in the way "
                        f"{expected_path_display} records. Aborting.",
                        file=sys.stderr,
                        flush=True,
                    )

                    # --- DEBUGGING BLOCK START ---
                    print("\n--- DIFF (Expected vs Actual) ---", file=sys.stderr)
                    diff = difflib.unified_diff(
                        expected_norm.splitlines(),
                        output_norm.splitlines(),
                        fromfile="Expected",
                        tofile="Actual",
                        lineterm="",
                    )
                    for line in diff:
                        print(line, file=sys.stderr)

                    print("\n--- RAW REPR CHECK ---", file=sys.stderr)
                    # This reveals hidden chars like \r or distinct unicode spaces
                    print(f"Expected len: {len(expected_norm)}", file=sys.stderr)
                    print(f"Actual len:   {len(output_norm)}", file=sys.stderr)
                    # --- DEBUGGING BLOCK END ---

                    return 1
            elif recording_new and result.return_code == ReturnCodes.SUCCESS:
                # Nothing to record: a file that passes validation is not a negative
                # fixture, and writing a snapshot of a *passing* run would invent one.
                # Not an error — a recording run is allowed to be pointed at a mixed
                # directory — but it must say what it decided.
                print(
                    f"⏭️  {test_path} passed validation (code {result.return_code}), so "
                    f"it is not a negative fixture. No snapshot written; it stays "
                    f"ordinary data for check-data-conformance.",
                    flush=True,
                )
                examined -= 1
                continue
            else:
                print(
                    f"\n❌ {test_path} is paired with {expected_path_display}, so it is "
                    f"expected to fail, but validation returned "
                    f"{result.return_code} instead of 210. Either the data no longer "
                    f"violates anything - delete the snapshot to treat it as ordinary "
                    f"data - or the snapshot is stale. Aborting.",
                    file=sys.stderr,
                    flush=True,
                )
                return result.return_code or 1

    if examined == 0 and require_fixtures:
        # The caller asked for these files to be checked as negative fixtures and none
        # of them were. Reporting success here is how a recording run that wrote no
        # snapshot, and a check that verified no file, both used to pass.
        print(
            "\n❌ Error: no negative fixtures were checked. A data file counts as one "
            "when a .expected snapshot sits beside it (same stem, .expected suffix); "
            "pass --update-expected to record the snapshots for files that fail.",
            file=sys.stderr,
            flush=True,
        )
        return ReturnCodes.GENERAL_ERROR

    if examined and update_expected:
        print(f"\n✅ {examined} negative fixture snapshot(s) recorded.", flush=True)
    elif examined:
        print(f"\n✅ {examined} negative fixture(s) behaved as recorded.", flush=True)

    return 0


def validate_artifact_coherence_all(
    ontology_domains: List[str],
    resolver: RegistryResolver = None,
) -> int:
    """
    Validate target classes against OWL for each domain.

    Args:
        ontology_domains: List of domain names to check
        resolver: Optional pre-configured RegistryResolver (with registered artifacts)

    Returns:
        0 on success, non-zero on failure
    """
    if not ontology_domains:
        return 0
    print("\n=== Checking target classes against OWL classes ===", flush=True)

    # Skip coherence check for temporary domains (no artifacts)
    domains_to_check = [
        d for d in ontology_domains if not d.startswith(TEMP_DOMAIN_PREFIX)
    ]
    if not domains_to_check:
        print("📋 Skipping coherence check (no artifact domains)", flush=True)
        return 0

    active_resolver = resolver if resolver else RegistryResolver(ROOT_DIR)
    root_dir = get_resolver_root_dir(active_resolver)

    for domain in domains_to_check:
        print(f"\n🔍 Checking target classes for domain: {domain}", flush=True)

        # Build known-issues set for this domain from KNOWN_COHERENCE_ISSUES
        known_set = {
            cls for (d, cls), url in KNOWN_COHERENCE_ISSUES.items() if d == domain
        }
        if known_set:
            urls = [
                url for (d, _), url in KNOWN_COHERENCE_ISSUES.items() if d == domain
            ]
            for url in urls:
                print(f"  ⚠️  Known upstream issue: {url}", flush=True)

        # Call the validator with resolver
        returncode, output = validate_artifact_coherence(
            domain,
            root_dir=root_dir,
            resolver=active_resolver,
            known_issues=known_set,
        )

        if output:
            target = sys.stdout if returncode == 0 else sys.stderr
            print(output, file=target, flush=True)

        if returncode != 0:
            print(
                f"\n❌ Error {returncode} during target class validation for {domain}. Aborting.",
                file=sys.stderr,
                flush=True,
            )
            return returncode
        else:
            print(f"✅ Target classes are correctly defined for {domain}.", flush=True)

    return 0


def _running_from_source_checkout() -> bool:
    """True when OMB's data root is a repository checkout rather than an install.

    An installed wheel carries its data inside the package (``omb/data/``); a checkout
    does not, and has the repository's own development files instead. ``pyproject.toml``
    beside the data root is the cheap, unambiguous marker.
    """
    return (builtin_data_root() / "pyproject.toml").is_file()


def check_environment(skip_env_check: bool = False) -> int:
    """Check the interpreter is usable and return a process exit code.

    Python version is a hard requirement: the code uses 3.12 syntax, so an older
    interpreter cannot run it at all.

    The virtual-environment check is a *development* guard, not a runtime requirement,
    and only applies when running from a source checkout — there, "not in a venv"
    almost always means the project's own ``.venv`` was not activated and the
    dependencies are missing or stale. It used to be a hard exit for everyone, which
    broke every legitimate way of running an installed package outside a venv: a
    container that pip-installs into the system interpreter, a CI runner that is not
    GitHub Actions (the one platform special-cased here), a ``pip install --user``.
    Worse, it ran before argument parsing, so even ``onto-validate --help`` exited 1.

    It is now a warning, and ``--skip-env-check`` — which this function's docstring has
    promised for some time without the flag existing — silences it.

    Returns:
        0 when the interpreter is usable, non-zero when it is not.
    """
    if sys.version_info < (3, 12):
        print(
            f"❌ Error: This project requires Python 3.12+. You are running {sys.version.split()[0]}.",
            file=sys.stderr,
        )
        return ReturnCodes.GENERAL_ERROR

    if skip_env_check:
        return ReturnCodes.SUCCESS

    in_venv = (sys.prefix != sys.base_prefix) or ("CONDA_DEFAULT_ENV" in os.environ)

    if not in_venv and _running_from_source_checkout():
        print(
            "⚠️  Warning: running from a source checkout without an active virtual "
            "environment. Dependencies may be missing or stale — `just setup` creates "
            "the project environment. Pass --skip-env-check to silence this.",
            file=sys.stderr,
        )

    return ReturnCodes.SUCCESS


# --- CLI / Main Logic ---
def main() -> int:
    """Run validation checks based on arguments and return a process exit code.

    Returns the code rather than calling ``sys.exit`` so both entry points agree: the
    ``onto-validate`` console script exits with what this returns, and ``python -m omb``
    passes it to ``SystemExit``. Previously it returned ``None`` and exited from the
    inside, which meant the console script's own exit status was always 0.
    """
    configure_cli_logging()
    ensure_utf8_output()

    # Argument Parsing
    # Use the module docstring (__doc__) as the description
    parser = argparse.ArgumentParser(
        prog="onto-validate",
        description=__doc__,  # <--- CHANGED: Uses the detailed docstring from the top of the file
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create argument groups for better organization
    mode_group = parser.add_argument_group("Validation Modes")
    target_group = parser.add_argument_group("Target Selection")

    mode_group.add_argument(
        "--run",
        type=str,
        choices=[
            "all",
            "check-syntax",
            "check-artifact-coherence",
            "check-data-conformance",
            "check-failing-tests",
        ],
        default="all",
        help="Validation mode to run (default: all)",
    )

    mode_group.add_argument(
        "--update-expected",
        action="store_true",
        default=False,
        help="check-failing-tests only: (re)record each negative test's .expected "
        "snapshot from the live validation report instead of comparing. Use after "
        "an intentional schema or OMB/pyshacl change, then review the diff.",
    )

    target_group.add_argument(
        "--domain",
        type=str,
        nargs="+",
        default=None,
        metavar="DOMAIN",
        help="Domain name(s) from catalog (e.g., manifest, scenario).",
    )

    target_group.add_argument(
        "--data-paths",
        type=str,
        nargs="+",
        default=None,
        metavar="PATH",
        help=(
            "Files or directories to validate. "
            "FILE: validates file, scans parent for fixtures. "
            "DIR: scans recursively, auto-detects top-level vs fixtures."
        ),
    )

    target_group.add_argument(
        "--artifacts",
        type=str,
        nargs="+",
        default=None,
        metavar="DIR",
        help="Additional artifact directories for schema discovery and context inlining.",
    )

    target_group.add_argument(
        "--inference-mode",
        type=str,
        choices=["rdfs", "owlrl", "none", "both"],
        default="rdfs",
        help="Inference mode for SHACL validation (default: rdfs).",
    )

    target_group.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Strict mode: unresolved IRIs cause validation failure.",
    )

    target_group.add_argument(
        "--allow-online",
        action="store_true",
        default=True,
        help="Allow online fallback for unresolved IRIs (enabled by default).",
    )

    target_group.add_argument(
        "--offline",
        dest="allow_online",
        action="store_false",
        help="Disable online fallback for unresolved IRIs.",
    )

    target_group.add_argument(
        "--remote",
        action="store_true",
        default=False,
        help="Enable HTTP artifact resolution for pip-only installations "
        "(fetches ontology schemas from GitHub Pages when local catalogs are missing).",
    )

    target_group.add_argument(
        "--fail-on-warnings",
        dest="allow_warnings",
        action="store_false",
        default=True,
        help="Treat sh:Warning and sh:Info results as failures. By default they "
        "are advisory: reported after the validation report, but not counted "
        "against conformance and never recorded into a .expected snapshot.",
    )

    target_group.add_argument(
        "--per-resource",
        dest="per_resource",
        action="store_true",
        default=False,
        help="Validate each data file in its own graph (no cross-document "
        "merging), sharing loaded shapes/ontology. Correct grain for Verifiable "
        "Credentials and DID documents that reuse IRIs across files.",
    )

    target_group.add_argument(
        "--skip-env-check",
        action="store_true",
        default=False,
        help="Silence the development warning about running from a source checkout "
        "without an active virtual environment. Installed packages never emit it.",
    )

    args = parser.parse_args()

    env_code = check_environment(skip_env_check=args.skip_env_check)
    if env_code != ReturnCodes.SUCCESS:
        return env_code

    _enable_http = args.remote

    # DATA PATHS MODE: User specified file/directory paths
    # Uses auto-discovery to detect top-level files vs fixtures
    data_paths = args.data_paths
    if data_paths:
        print("🔍 Data paths mode: Auto-discovering files to validate", flush=True)

        # Validate that paths exist
        valid_paths = []
        for p in data_paths:
            if Path(p).exists():
                valid_paths.append(p)
            else:
                display_path = str(p).replace("\\", "/")
                print(
                    f"⚠️  Warning: Path does not exist: {display_path}",
                    file=sys.stderr,
                )

        if len(valid_paths) != len(data_paths):
            return ReturnCodes.GENERAL_ERROR

        if not valid_paths:
            print("❌ Error: No valid paths provided.", file=sys.stderr)
            return ReturnCodes.GENERAL_ERROR

        # Auto-discover top-level files and fixture mappings
        top_level_files, iri_to_file, metadata = discover_data_hierarchy(
            valid_paths, include_did_documents=True
        )

        if not top_level_files:
            print("❌ Error: No JSON-LD data files found to validate.", file=sys.stderr)
            return ReturnCodes.GENERAL_ERROR

        print(f"   Found {len(top_level_files)} top-level file(s) to validate")
        print(f"   Found {metadata['fixture_count']} fixture(s) for IRI resolution")

        # Warn about duplicate IDs
        if metadata["duplicate_ids"]:
            print(
                f"   ⚠️  Warning: {len(metadata['duplicate_ids'])} duplicate ID(s) found:"
            )
            for dup_id, dup_files in metadata["duplicate_ids"]:
                file_names = ", ".join(f.name for f in dup_files)
                print(f"      - {dup_id}: {file_names}")

        # Create catalog resolver
        catalog_resolver = RegistryResolver(ROOT_DIR, enable_http=_enable_http)

        # Register discovered fixtures for IRI resolution
        if iri_to_file:
            catalog_resolver.register_fixture_mappings(iri_to_file)

        # Register additional artifact directories for schema discovery
        artifact_dir_paths = []
        if args.artifacts:
            for ad in args.artifacts:
                ad_path = Path(ad).resolve()
                if ad_path.is_dir():
                    registered = catalog_resolver.register_artifact_directory(ad_path)
                    if registered:
                        artifact_dir_paths.append(ad_path)
                        print(
                            f"📦 Registered artifact domains: {', '.join(registered)}",
                            flush=True,
                        )
                    else:
                        # Silence here meant a misnamed or half-generated artifacts
                        # directory looked exactly like a correct one, all the way to
                        # "validation passed".
                        print(
                            f"⚠️  Warning: no artifact domains found in {ad}. Expected "
                            f"{ad}/{{domain}}/{{domain}}.owl.ttl (plus .shacl.ttl, "
                            f".context.jsonld).",
                            file=sys.stderr,
                            flush=True,
                        )
                else:
                    print(
                        f"⚠️  Warning: Artifact directory does not exist: {ad}",
                        file=sys.stderr,
                    )

        # Discovery includes all requested documents, while sibling files are only
        # registered for reference resolution. Per-resource uses these same inputs.
        domain_files = list(top_level_files)
        # A recording run classifies every named file as a candidate negative fixture:
        # the snapshot that normally does the classifying is the very thing it is about
        # to write. Only for `--run check-failing-tests --update-expected`, so an
        # ordinary run still keeps the snapshot-pairing rule as the single criterion.
        recording_run = args.update_expected and args.run == "check-failing-tests"
        temp_domain = catalog_resolver.create_temporary_domain(
            domain_files, treat_all_as_negative=recording_run
        )

        if not temp_domain:
            print("❌ Error: Failed to create temporary domain.", file=sys.stderr)
            return ReturnCodes.GENERAL_ERROR

        # Use temporary domain like a regular catalog domain
        ontology_domains = [temp_domain]

    # DOMAIN MODE: User specified catalog domains
    elif args.domain is not None:
        print(f"🔍 Domain mode: Using catalog for domain(s): {args.domain}", flush=True)
        catalog_resolver = RegistryResolver(ROOT_DIR, enable_http=_enable_http)

        # Register additional artifact directories (before checking domains)
        if args.artifacts:
            for ad in args.artifacts:
                ad_path = Path(ad).resolve()
                if ad_path.is_dir():
                    registered = catalog_resolver.register_artifact_directory(ad_path)
                    if registered:
                        print(
                            f"📦 Registered artifact domains: {', '.join(registered)}",
                            flush=True,
                        )
                else:
                    print(
                        f"⚠️  Warning: Artifact directory does not exist: {ad}",
                        file=sys.stderr,
                    )

        # Get available domains (including registered artifacts)
        available_domains = set(catalog_resolver.get_test_domains())
        # Also include artifact domains for coherence checks
        artifact_domains = set(catalog_resolver.get_artifact_domains())
        all_available = available_domains | artifact_domains

        ontology_domains = [d for d in args.domain if d in all_available]

        if not ontology_domains and len(args.domain) > 0:
            print(f"⚠️ None of the provided domains exist: {args.domain}")
            print("Available test domains:", sorted(available_domains))
            if artifact_domains:
                print("Available artifact domains:", sorted(artifact_domains))
            return ReturnCodes.GENERAL_ERROR

        print(f"Detected ontology domains: {ontology_domains}", flush=True)

    # AUTO MODE: Discover all domains from catalog
    else:
        print("🔍 Auto mode: Discovering all domains from catalog", flush=True)
        catalog_resolver = RegistryResolver(ROOT_DIR, enable_http=_enable_http)
        ontology_domains = catalog_resolver.get_test_domains()

        if not ontology_domains:
            print("No ontology domains to check in tests/catalog-v001.xml. Exiting.")
            return ReturnCodes.SUCCESS

        print(f"Detected ontology domains: {ontology_domains}", flush=True)

    # 5. Define validation checks
    # Both path mode and domain mode use the same catalog-based functions
    # (path mode creates a temporary catalog domain)
    _inference_mode = args.inference_mode
    _strict = args.strict
    _allow_online = args.allow_online
    _per_resource = args.per_resource

    # Artifact coherence requires standard catalog structure with domain
    # artifacts, so it stays unsupported in data-paths mode. check-failing-tests
    # DOES work in data-paths mode: create_temporary_domain registers a supplied file
    # as invalid test-data when a `.expected` snapshot sits beside it.
    if data_paths and args.run == "check-artifact-coherence":
        print(
            f"❌ Error: {args.run} is not supported in data-paths mode.",
            file=sys.stderr,
        )
        print(
            "   This check requires catalog structure with domain artifacts.",
            file=sys.stderr,
        )
        return ReturnCodes.GENERAL_ERROR

    check_map = {
        "check-syntax": [
            (
                "Check Syntax",
                lambda: check_syntax_all(ontology_domains, catalog_resolver),
            )
        ],
        "check-artifact-coherence": [
            (
                "Check Artifact Coherence",
                lambda: validate_artifact_coherence_all(
                    ontology_domains, catalog_resolver
                ),
            )
        ],
        "check-data-conformance": [
            (
                "Check Data Conformance",
                lambda: validate_data_conformance_all(
                    ontology_domains,
                    catalog_resolver,
                    _inference_mode,
                    strict=_strict,
                    allow_online=_allow_online,
                    per_resource=_per_resource,
                    allow_warnings=args.allow_warnings,
                ),
            )
        ],
        "check-failing-tests": [
            (
                "Check Failing Tests",
                lambda: check_failing_tests_all(
                    ontology_domains,
                    catalog_resolver,
                    _inference_mode,
                    allow_online=_allow_online,
                    update_expected=args.update_expected,
                    allow_warnings=args.allow_warnings,
                    # Only when the user named both the files and this check: then
                    # "no negative fixtures found" is a failed request, not an empty
                    # one. Under `--run all`, or in domain mode, having none is normal.
                    require_fixtures=bool(data_paths)
                    and args.run == "check-failing-tests",
                ),
            )
        ],
    }

    if args.run == "all":
        if data_paths:
            # Only artifact coherence is skipped, for the reason given above. Failing
            # tests must run: ``create_temporary_domain`` registers supplied files under
            # an ``invalid/`` directory as negative fixtures, which data conformance then
            # skips. Leaving this check out meant such a file was validated by nothing at
            # all while the suite still reported success.
            checks_to_run = (
                check_map["check-syntax"]
                + check_map["check-data-conformance"]
                + check_map["check-failing-tests"]
            )
        else:
            checks_to_run = (
                check_map["check-syntax"]
                + check_map["check-artifact-coherence"]
                + check_map["check-data-conformance"]
                + check_map["check-failing-tests"]
            )
    else:
        checks_to_run = check_map[args.run]

    print(f"\n🚀 Running check mode: {args.run.upper()} ...", flush=True)

    for name, phase_func in checks_to_run:
        rc = phase_func()
        if rc != 0:
            print(
                f"\n❌ {name} phase failed (code {rc}). Aborting.",
                file=sys.stderr,
                flush=True,
            )
            return rc

    print(f"\n✅ {args.run.upper()} checks completed successfully!", flush=True)


if __name__ == "__main__":
    # UTF-8 output is set up inside main() (see ensure_utf8_output), so the console
    # script and `python -m omb` get it too — not only this path.
    raise SystemExit(main())
