#!/usr/bin/env python3
"""
Unit tests for hooks.normalize_linkml_output.
"""

import importlib.util
import json
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "hooks"
    / "normalize_linkml_output.py"
)
SPEC = importlib.util.spec_from_file_location("normalize_linkml_output", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
normalize_json_document = MODULE.normalize_json_document


def test_normalize_json_document_removes_extra_blank_lines(temp_dir: Path):
    context_file = temp_dir / "sample.context.jsonld"
    context_file.write_text(
        '{\n   "@context": {\n      "@vocab": "http://example.org/"\n   }\n}\n\n',
        encoding="utf-8",
    )

    normalize_json_document(context_file)

    expected = (
        json.dumps(
            {"@context": {"@vocab": "http://example.org/"}},
            indent=3,
            ensure_ascii=False,
        )
        + "\n"
    )
    assert context_file.read_text(encoding="utf-8") == expected
