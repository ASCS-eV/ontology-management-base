#!/usr/bin/env python3
"""Pure, side-effect-free validation API for OMB.

FEATURE SET:
============
1. validate_data - Validate JSON-LD data paths and return a ValidationResult

USAGE:
======
    from omb.api import validate_data

    result = validate_data(["tests/data/gx/valid"])
    if result.conforms:
        handle_success(result)

DEPENDENCIES:
=============
- pathlib: For path handling
- omb validators and registry utilities

NOTES:
======
- No printing, no argparse, and no sys.exit.
- Callers decide how to render results and which process code to return.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Sequence

from omb.core.result import ReturnCodes, ValidationResult
from omb.utils.registry_resolver import RegistryResolver
from omb.validators.shacl.validator import ShaclValidator
from omb.validators.validation_suite import ROOT_DIR, discover_data_hierarchy


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
    """
    active_root = root_dir or ROOT_DIR
    valid_paths = [Path(path) for path in data_paths if Path(path).exists()]

    if not valid_paths:
        return _error_result("No valid paths provided")

    top_level_files, iri_to_file, metadata = discover_data_hierarchy(valid_paths)
    duplicate_warnings = _duplicate_warnings(metadata.get("duplicate_ids", []))

    if not top_level_files:
        result = _error_result("No top-level files found to validate")
        result.warnings.extend(duplicate_warnings)
        return result

    resolver = RegistryResolver(active_root, enable_http=enable_http)

    if iri_to_file:
        resolver.register_fixture_mappings(iri_to_file)

    for artifact in artifacts or []:
        artifact_path = Path(artifact).resolve()
        if artifact_path.is_dir():
            resolver.register_artifact_directory(artifact_path)

    domain_files = list(top_level_files)
    if per_resource and iri_to_file:
        existing = {Path(file_path).resolve() for file_path in domain_files}
        fixture_files = sorted(
            {Path(file_path).resolve() for file_path in iri_to_file.values()}
        )
        domain_files += [
            file_path for file_path in fixture_files if file_path not in existing
        ]

    with _info_logging_disabled():
        temp_domain = resolver.create_temporary_domain(domain_files)

    if not temp_domain:
        result = _error_result("Failed to create temporary domain")
        result.warnings.extend(duplicate_warnings)
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

    result.warnings.extend(duplicate_warnings)
    return result


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
    duplicate_ids: Sequence[tuple[str, Sequence[Path]]],
) -> list[str]:
    """Format duplicate ID metadata as warning strings."""
    return [
        f"Duplicate ID {duplicate_id}: {', '.join(file_path.name for file_path in files)}"
        for duplicate_id, files in duplicate_ids
    ]


@contextmanager
def _info_logging_disabled() -> Iterator[None]:
    """Temporarily suppress INFO-and-below logging emitted by reused helpers."""
    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.INFO)
    try:
        yield
    finally:
        logging.disable(previous_disable_level)
