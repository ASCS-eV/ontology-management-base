#!/usr/bin/env python3
"""
Unit tests for src.tools.validators.syntax_validator.

The unified API returns (overall_code, [(file_code, file_msg), ...]) for all functions.
"""

import json
from pathlib import Path

from src.tools.core.result import ReturnCodes
from src.tools.validators import syntax_validator


def test_check_json_syntax_success(temp_dir: Path):
    file_path = temp_dir / "ok.json"
    file_path.write_text(json.dumps({"a": 1}))
    code, results = syntax_validator.check_json_wellformedness(file_path)
    assert code == ReturnCodes.SUCCESS
    assert len(results) == 1
    assert results[0][0] == ReturnCodes.SUCCESS
    assert "Syntax OK" in results[0][1]


def test_check_json_syntax_error(temp_dir: Path):
    file_path = temp_dir / "bad.json"
    file_path.write_text("{bad json}")
    code, results = syntax_validator.check_json_wellformedness(file_path)
    assert code == ReturnCodes.JSON_SYNTAX_ERROR
    assert len(results) == 1
    assert results[0][0] == ReturnCodes.JSON_SYNTAX_ERROR
    assert "Syntax Error" in results[0][1]


def test_verify_json_syntax_no_files_returns_error():
    code, results = syntax_validator.check_json_wellformedness(["nonexistent_path"])
    assert code == ReturnCodes.GENERAL_ERROR
    assert results


def test_check_turtle_syntax_success(temp_dir: Path):
    file_path = temp_dir / "ok.ttl"
    file_path.write_text(
        "<http://example.org/a> <http://example.org/p> <http://example.org/o> ."
    )
    code, results = syntax_validator.check_turtle_wellformedness(file_path)
    assert code == ReturnCodes.SUCCESS
    assert len(results) == 1
    assert results[0][0] == ReturnCodes.SUCCESS
    assert "Syntax OK" in results[0][1]


def test_check_turtle_syntax_error(temp_dir: Path):
    file_path = temp_dir / "bad.ttl"
    file_path.write_text("not turtle")
    code, results = syntax_validator.check_turtle_wellformedness(file_path)
    assert code == ReturnCodes.TURTLE_SYNTAX_ERROR
    assert len(results) == 1
    assert results[0][0] == ReturnCodes.TURTLE_SYNTAX_ERROR
    assert "Syntax Error" in results[0][1] or "Unexpected error" in results[0][1]


def test_check_all_wellformedness_multiple_files(temp_dir: Path):
    """Test batch validation of multiple files."""
    json_file = temp_dir / "data.json"
    json_file.write_text('{"key": "value"}')
    ttl_file = temp_dir / "data.ttl"
    ttl_file.write_text("<http://ex.org/a> a <http://ex.org/B> .")

    code, results = syntax_validator.check_all_wellformedness(temp_dir)
    assert code == ReturnCodes.SUCCESS
    assert len(results) == 2  # One JSON, one TTL
