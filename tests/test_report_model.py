#!/usr/bin/env python3
"""Tests for structured ValidationResult routing metadata."""

from pathlib import Path

from src.tools.api import validate_data

GX_VALID_DIR = Path("tests/data/gx/valid")


def _assert_populated_metadata(result):
    """Assert the report-model routing fields are populated for gx fixtures."""
    assert result.shapes_loaded > 0
    assert result.target_types
    assert result.types_unrouted == []
    assert result.types_routed
    assert all(count > 0 for count in result.per_type_shape_count.values())


def test_report_model_happy_path_populates_metadata():
    """A successful gx validation should expose shape/type routing metadata."""
    result = validate_data([GX_VALID_DIR])

    assert result.conforms is True
    assert result.return_code == 0
    _assert_populated_metadata(result)


def test_report_model_per_resource_carries_metadata():
    """Per-resource aggregation should preserve routing metadata."""
    result = validate_data([GX_VALID_DIR], per_resource=True)

    _assert_populated_metadata(result)


def test_report_model_error_path_uses_defaults():
    """An early error result should keep routing metadata at safe defaults."""
    result = validate_data(["does/not/exist"])

    assert result.shapes_loaded == 0
    assert result.target_types == []
    assert result.types_unrouted == []
    assert result.per_type_shape_count == {}


def test_report_model_field_types_are_stable():
    """Routing metadata fields should expose list and dict types for callers."""
    result = validate_data([GX_VALID_DIR])

    assert isinstance(result.per_type_shape_count, dict)
    assert isinstance(result.target_types, list)
