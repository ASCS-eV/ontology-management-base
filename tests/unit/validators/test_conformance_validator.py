#!/usr/bin/env python3
"""
Unit tests for src.tools.validators.conformance_validator.
"""

from pathlib import Path

from src.tools.core.result import ReturnCodes
from src.tools.validators import conformance_validator
from src.tools.validators.conformance_validator import (
    collect_jsonld_files,
    validate_files,
)


def test_collect_jsonld_files_empty_returns_empty():
    assert collect_jsonld_files([]) == []


def test_validate_files_no_files_returns_error(temp_dir: Path):
    result = validate_files([str(temp_dir)])
    assert result.return_code == ReturnCodes.GENERAL_ERROR
    assert "No JSON-LD files found" in result.report_text


def test_validate_data_conformance_forwards_artifact_dirs(monkeypatch, temp_dir: Path):
    captured = {}

    def _fake_validate(
        jsonld_files,
        root_dir,
        inference_mode="rdfs",
        debug=False,
        logfile=None,
        artifact_dirs=None,
    ):
        captured["jsonld_files"] = jsonld_files
        captured["root_dir"] = root_dir
        captured["inference_mode"] = inference_mode
        captured["artifact_dirs"] = artifact_dirs
        return 0, "ok"

    monkeypatch.setattr(
        conformance_validator, "_validate_data_conformance", _fake_validate
    )

    artifact_dir = temp_dir / "external-artifacts"
    return_code, output = conformance_validator.validate_data_conformance(
        [Path("sample.json")],
        temp_dir,
        artifact_dirs=[artifact_dir],
    )

    assert return_code == 0
    assert output == "ok"
    assert captured["jsonld_files"] == [Path("sample.json")]
    assert captured["root_dir"] == temp_dir
    assert captured["artifact_dirs"] == [artifact_dir]
