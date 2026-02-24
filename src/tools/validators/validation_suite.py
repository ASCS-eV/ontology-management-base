#!/usr/bin/env python3
"""
Validation Suite for Ontology Management Base

This script acts as the central entry point for validating ontology artifacts,
SHACL shapes, and test data. It ensures that changes to the ontology structure
or data definitions comply with defined standards.

PREREQUISITES:
=============
- Python 3.12 or higher
- Active Virtual Environment (venv, conda, etc.)
- Catalogs must be generated (run: python -m src.tools.utils.registry_updater)

OPERATION MODES:
===============

1. AUTO DISCOVERY MODE (Default)
   Scans the test catalog (tests/catalog-v001.xml) and validates ALL registered domains.
   Usage:
     python3 -m src.tools.validators.validation_suite

2. DOMAIN SELECTION MODE
   Restricts catalog-based validation to specific domains.
   Usage:
     python3 -m src.tools.validators.validation_suite --domain manifest
     python3 -m src.tools.validators.validation_suite --domain manifest scenario

3. DATA PATHS MODE
   Validates arbitrary files or directories with auto-discovery of fixtures.
   Usage:
     python3 -m src.tools.validators.validation_suite --data-paths tests/data/manifest/valid/
     python3 -m src.tools.validators.validation_suite --data-paths ./my_data.json

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
      python3 -m src.tools.validators.validation_suite --data-paths ./my-data.json \\
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
    (Catalog/Domain Mode only)
    Executes "Negative Tests" - data files expected to fail validation.
    Verifies that they fail with the specific error code/message defined in .expected files.

EXAMPLES:
=========
# Run everything on the whole repository
python3 -m src.tools.validators.validation_suite

# Check only syntax for the 'manifest' domain
python3 -m src.tools.validators.validation_suite --run check-syntax --domain manifest

# Validate data with auto-discovery of fixtures
python3 -m src.tools.validators.validation_suite --run check-data-conformance \\
    --data-paths ./examples/

# Validate a single file (parent dir scanned for fixtures)
python3 -m src.tools.validators.validation_suite --run check-data-conformance \\
    --data-paths ./examples/my-data.json --artifacts ./artifacts
"""

import argparse
import difflib
import io
import os
import sys
from pathlib import Path
from typing import List

from src.tools.utils.file_collector import discover_data_hierarchy
from src.tools.utils.print_formatter import normalize_path_for_display, normalize_text
from src.tools.utils.registry_resolver import TEMP_DOMAIN_PREFIX, RegistryResolver
from src.tools.validators.coherence_validator import validate_artifact_coherence
from src.tools.validators.shacl.validator import ShaclValidator
from src.tools.validators.syntax_validator import (
    check_json_wellformedness,
    check_turtle_wellformedness,
)

# Default root directory (computed from module location).
# Functions accept root_dir as parameter; this is only used as fallback.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Known upstream coherence failures that should warn instead of fail.
# Maps (domain, lowercase_class_name) -> upstream issue URL.
# Remove entries once the upstream issue is resolved.
KNOWN_COHERENCE_ISSUES = {
    ("gx", "consent"): (
        "https://gitlab.com/gaia-x/technical-committee/"
        "service-characteristics-working-group/service-characteristics/-/issues/353"
    ),
}


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
        code, results = check_json_wellformedness(json_file, ROOT_DIR)
        for c, msg in results:
            if c != 0:
                print(msg, file=sys.stderr)
                return c
            print(msg)

    print("\n=== Checking TTL syntax ===", flush=True)

    # Check TTL files
    if ttl_files_to_check:
        for ttl_file in sorted(set(ttl_files_to_check)):
            code, results = check_turtle_wellformedness(ttl_file, ROOT_DIR)
            for c, msg in results:
                if c != 0:
                    print(msg, file=sys.stderr)
                    return c
                print(msg)
    else:
        print("  No TTL files in catalog to check")

    print("📌 Completed TTL and JSON syntax tests", flush=True)
    return 0


def validate_data_conformance_all(
    ontology_domains: List[str],
    resolver: RegistryResolver = None,
    inference_mode: str = "rdfs",
    strict: bool = False,
    allow_online: bool = False,
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

    Returns:
        0 on success, non-zero on failure
    """
    if not ontology_domains:
        return 0
    print("\n=== Checking JSON-LD against SHACL ===", flush=True)

    catalog_resolver = resolver if resolver else RegistryResolver(ROOT_DIR)

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
    validator = ShaclValidator(
        ROOT_DIR,
        inference_mode=inference_mode,
        verbose=True,
        resolver=catalog_resolver,
        strict=strict,
        allow_online=allow_online,
    )

    for domain in ontology_domains:
        print(
            f"\n🔍 Starting JSON-LD SHACL validation for domain: {domain}", flush=True
        )

        # Use catalog-based validation method
        try:
            result = validator.validate_from_catalog(domain, test_type="valid")
        except (RuntimeError, ValueError) as e:
            print(f"\n\u274c {e}", file=sys.stderr, flush=True)
            return 1

        if not result.files_validated:
            print(f"⚠️ No JSON-LD files found in '{domain}'. Skipping.", flush=True)
            continue

        print(f"   Found {len(result.files_validated)} test files from catalog")

        if result.return_code != 0:
            print("\n📄 SHACL validation report:", flush=True)
            print(validator.format_result(result), flush=True)

            print(
                f"\n❌ Error during JSON-LD SHACL validation for domain '{domain}'. Aborting.",
                file=sys.stderr,
                flush=True,
            )
            return result.return_code
        else:
            print(f"\n✅ {domain} conforms to SHACL constraints.", flush=True)

    return 0


def check_failing_tests_all(
    ontology_domains: List[str],
    resolver: RegistryResolver = None,
    inference_mode: str = "rdfs",
    allow_online: bool = False,
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

    Returns:
        0 on success, non-zero on failure
    """
    if not ontology_domains:
        return 0
    print("\n=== Running failing tests ===", flush=True)

    catalog_resolver = resolver if resolver else RegistryResolver(ROOT_DIR)

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
    validator = ShaclValidator(
        ROOT_DIR,
        inference_mode=inference_mode,
        verbose=True,
        resolver=catalog_resolver,
        allow_online=allow_online,
    )

    for domain in ontology_domains:
        print(f"\n🔍 Running failing tests for domain: {domain}", flush=True)

        invalid_test_files = catalog_resolver.get_test_files(
            domain, test_type="invalid"
        )
        if not invalid_test_files:
            continue

        for test_abs_path in invalid_test_files:
            test_abs_path = Path(test_abs_path)
            test_path = normalize_path_for_display(test_abs_path, ROOT_DIR)
            expected_output_path = test_abs_path.with_suffix("").with_suffix(
                ".expected"
            )

            if not expected_output_path.exists():
                expected_path_display = normalize_path_for_display(
                    expected_output_path, ROOT_DIR
                )
                print(
                    f"⚠️ No expected output file found: {expected_path_display}",
                    file=sys.stderr,
                    flush=True,
                )
                return 1

            expected_output = expected_output_path.read_text(encoding="utf-8").strip()

            print(f"🔍 Running failing test: {test_path}", flush=True)

            # Validate single file (fixtures/schemas resolved via catalog)
            result = validator.validate([test_abs_path])
            output = validator.format_result(result)
            print(output)
            print("\n", flush=True)

            if result.return_code == 210:
                output_norm = normalize_text(output)
                expected_norm = normalize_text(expected_output)

                if output_norm == expected_norm:
                    print(
                        f"✅ Test {test_path} for domain {domain} failed as expected.",
                        flush=True,
                    )
                else:
                    print(
                        f"\n❌ Error: Output discrepancy for {test_path}. Aborting.",
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
            else:
                print(
                    f"\n❌ Test {test_path} did not return code 210 (got {result.return_code}). Aborting.",
                    file=sys.stderr,
                    flush=True,
                )
                return result.return_code or 1

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
            domain, root_dir=ROOT_DIR, resolver=resolver, known_issues=known_set
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


def check_environment() -> None:
    """Enforce Python version and virtual environment requirements.

    Skips virtual-environment check when running in CI (``GITHUB_ACTIONS``
    env var set) or when ``--skip-env-check`` is passed.
    """
    if sys.version_info < (3, 12):
        print(
            f"❌ Error: This project requires Python 3.12+. You are running {sys.version.split()[0]}.",
            file=sys.stderr,
        )
        sys.exit(1)

    in_venv = (
        (sys.prefix != sys.base_prefix)
        or ("CONDA_DEFAULT_ENV" in os.environ)
        or ("GITHUB_ACTIONS" in os.environ)
    )

    if not in_venv:
        print(
            "❌ Error: You are NOT running inside a virtual environment.",
            file=sys.stderr,
        )
        sys.exit(1)


# --- CLI / Main Logic ---
def main():
    """Run validation checks based on arguments."""

    check_environment()

    # Argument Parsing
    # Use the module docstring (__doc__) as the description
    parser = argparse.ArgumentParser(
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
        default=False,
        help="Allow online fallback for unresolved IRIs (disabled by default).",
    )

    args = parser.parse_args()

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

        if not valid_paths:
            print("❌ Error: No valid paths provided.", file=sys.stderr)
            sys.exit(1)

        # Auto-discover top-level files and fixture mappings
        top_level_files, iri_to_file, metadata = discover_data_hierarchy(valid_paths)

        if not top_level_files:
            print("❌ Error: No top-level files found to validate.", file=sys.stderr)
            sys.exit(1)

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
        catalog_resolver = RegistryResolver(ROOT_DIR)

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
                    print(
                        f"⚠️  Warning: Artifact directory does not exist: {ad}",
                        file=sys.stderr,
                    )

        # Create temporary domain with top-level files only
        temp_domain = catalog_resolver.create_temporary_domain(
            [str(f) for f in top_level_files]
        )

        if not temp_domain:
            print("❌ Error: Failed to create temporary domain.", file=sys.stderr)
            sys.exit(1)

        # Use temporary domain like a regular catalog domain
        ontology_domains = [temp_domain]

    # DOMAIN MODE: User specified catalog domains
    elif args.domain is not None:
        print(f"🔍 Domain mode: Using catalog for domain(s): {args.domain}", flush=True)
        catalog_resolver = RegistryResolver(ROOT_DIR)

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
            sys.exit(1)

        print(f"Detected ontology domains: {ontology_domains}", flush=True)

    # AUTO MODE: Discover all domains from catalog
    else:
        print("🔍 Auto mode: Discovering all domains from catalog", flush=True)
        catalog_resolver = RegistryResolver(ROOT_DIR)
        ontology_domains = catalog_resolver.get_test_domains()

        if not ontology_domains:
            print("No ontology domains to check in tests/catalog-v001.xml. Exiting.")
            sys.exit(0)

        print(f"Detected ontology domains: {ontology_domains}", flush=True)

    # 5. Define validation checks
    # Both path mode and domain mode use the same catalog-based functions
    # (path mode creates a temporary catalog domain)
    _inference_mode = args.inference_mode
    _strict = args.strict
    _allow_online = args.allow_online

    # Artifact coherence and failing tests require standard domain structure
    if data_paths and args.run in ["check-artifact-coherence", "check-failing-tests"]:
        print(
            f"❌ Error: {args.run} is not supported in data-paths mode.",
            file=sys.stderr,
        )
        print(
            "   These checks require catalog structure with domain artifacts.",
            file=sys.stderr,
        )
        sys.exit(1)

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
                ),
            )
        ],
    }

    if args.run == "all":
        if data_paths:
            # Path mode: skip artifact coherence and failing tests
            checks_to_run = (
                check_map["check-syntax"] + check_map["check-data-conformance"]
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
            sys.exit(rc)

    print(f"\n✅ {args.run.upper()} checks completed successfully!", flush=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
