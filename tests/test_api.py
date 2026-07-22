#!/usr/bin/env python3
"""Tests for src.tools.api."""

import contextlib
import io
from pathlib import Path

from src.tools.api import validate_data
from src.tools.core.result import ValidationResult

GX_VALID_DIR = Path("tests/data/gx/valid")


def test_validate_data_valid_fixture_dir_returns_success():
    """A known-valid non-vacuous fixture directory should validate successfully."""
    result = validate_data([GX_VALID_DIR])

    assert result.conforms is True
    assert result.return_code == 0
    assert len(result.files_validated) >= 1


def test_validate_data_produces_no_stdout_or_stderr():
    """validate_data() should be pure with respect to stdout and stderr."""
    out = io.StringIO()
    err = io.StringIO()

    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        result = validate_data([GX_VALID_DIR])

    assert out.getvalue() == ""
    assert err.getvalue() == ""
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
