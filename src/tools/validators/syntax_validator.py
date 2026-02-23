#!/usr/bin/env python3
"""
Syntax Validator - Unified JSON-LD and Turtle Syntax Validation

This module validates that files are syntactically well-formed (parseable).
It does NOT validate logical structure, SHACL compliance, or semantic correctness.

API OVERVIEW:
=============

    check_json_wellformedness(paths, root_dir) -> (code, [(code, msg), ...])
    check_turtle_wellformedness(paths, root_dir) -> (code, [(code, msg), ...])
    check_all_wellformedness(paths, root_dir) -> (code, [(code, msg), ...])

All functions accept either:
- A single file path (str or Path)
- A list of file paths and/or directories (recursively searched)

USAGE:
======
    from src.tools.validators.syntax_validator import (
        check_json_wellformedness,
        check_turtle_wellformedness,
        check_all_wellformedness,
    )

    # Single file
    code, results = check_json_wellformedness("data/instance.json")

    # Multiple paths (files and directories)
    code, results = check_json_wellformedness(["data/", "examples/file.json"])
    code, results = check_turtle_wellformedness(["artifacts/"])

    # Both formats at once
    code, results = check_all_wellformedness(["artifacts/", "data/"])

STANDALONE TESTING:
==================
    python3 -m src.tools.validators.syntax_validator [--test] [--json] [--turtle] paths...

RETURN CODES:
=============
    0 = SUCCESS (all files valid)
    Non-zero = Error (see src.tools.core.result.ReturnCodes)
"""

import argparse
import io
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union

from rdflib import Graph
from rdflib.exceptions import ParserError

from src.tools.core.result import ReturnCodes
from src.tools.utils.file_collector import (
    PathsInput,
    collect_jsonld_files,
    collect_turtle_files,
)
from src.tools.utils.print_formatter import normalize_path_for_display


def _check_single_json(
    filename: Union[str, Path],
    root_dir: Optional[Path] = None,
) -> Tuple[int, str]:
    """Check a single JSON file for well-formedness."""
    if root_dir:
        display_path = normalize_path_for_display(filename, root_dir)
    else:
        display_path = str(filename)

    if not Path(filename).is_file():
        return ReturnCodes.JSON_SYNTAX_ERROR, f"File not found: {display_path}"

    try:
        with open(filename, "r", encoding="utf-8") as f:
            json.load(f)
        return ReturnCodes.SUCCESS, f"Syntax OK: {display_path}"
    except json.JSONDecodeError as e:
        msg = f"Syntax Error in {display_path}:\n   Line {e.lineno}, Col {e.colno}: {e.msg}"
        return ReturnCodes.JSON_SYNTAX_ERROR, msg
    except Exception as e:
        msg = f"Unexpected error parsing {display_path}:\n{e}"
        return ReturnCodes.JSON_SYNTAX_ERROR, msg


def _check_single_turtle(
    filename: Union[str, Path],
    root_dir: Optional[Path] = None,
) -> Tuple[int, str]:
    """Check a single Turtle file for well-formedness."""
    if root_dir:
        display_path = normalize_path_for_display(filename, root_dir)
    else:
        display_path = str(filename)

    if not Path(filename).is_file():
        return ReturnCodes.TURTLE_SYNTAX_ERROR, f"File not found: {display_path}"

    try:
        g = Graph()
        g.parse(filename, format="turtle")
        return ReturnCodes.SUCCESS, f"Syntax OK: {display_path}"
    except ParserError as e:
        msg = f"Syntax Error in {display_path}:\n{e}"
        return ReturnCodes.TURTLE_SYNTAX_ERROR, msg
    except Exception as e:
        msg = f"Unexpected error parsing {display_path}:\n{e}"
        return ReturnCodes.TURTLE_SYNTAX_ERROR, msg


# =============================================================================
# Public API
# =============================================================================


def check_json_wellformedness(
    paths: PathsInput,
    root_dir: Optional[Path] = None,
) -> Tuple[int, List[Tuple[int, str]]]:
    """
    Check JSON/JSON-LD files for syntactic well-formedness.

    Accepts a single file, a list of files, or directories (recursively searched
    for .json and .jsonld files).

    Args:
        paths: File path(s) or directory path(s) to check
        root_dir: Optional root directory for path normalization in output

    Returns:
        (return_code, results) tuple where:
        - return_code is 0 if all files are valid, non-zero otherwise
        - results is a list of (code, message) tuples for each file
    """
    results = []
    files = collect_jsonld_files(paths, warn_on_invalid=True, return_pathlib=False)

    if not files:
        msg = "No JSON-LD files found to check."
        results.append((ReturnCodes.GENERAL_ERROR, msg))
        return ReturnCodes.GENERAL_ERROR, results

    ret = 0
    for filename in files:
        filename = str(Path(filename).resolve())
        code, msg = _check_single_json(filename, root_dir)
        results.append((code, msg))
        ret |= code

    return ret, results


def check_turtle_wellformedness(
    paths: PathsInput,
    root_dir: Optional[Path] = None,
) -> Tuple[int, List[Tuple[int, str]]]:
    """
    Check Turtle files for syntactic well-formedness.

    Accepts a single file, a list of files, or directories (recursively searched
    for .ttl files).

    Args:
        paths: File path(s) or directory path(s) to check
        root_dir: Optional root directory for path normalization in output

    Returns:
        (return_code, results) tuple where:
        - return_code is 0 if all files are valid, non-zero otherwise
        - results is a list of (code, message) tuples for each file
    """
    results = []
    files = collect_turtle_files(paths, warn_on_invalid=True, return_pathlib=False)

    if not files:
        msg = "No Turtle files found to check."
        results.append((ReturnCodes.GENERAL_ERROR, msg))
        return ReturnCodes.GENERAL_ERROR, results

    ret = 0
    for filename in files:
        filename = str(Path(filename).resolve())
        code, msg = _check_single_turtle(filename, root_dir)
        results.append((code, msg))
        ret |= code

    return ret, results


def check_all_wellformedness(
    paths: PathsInput,
    root_dir: Optional[Path] = None,
    check_json: bool = True,
    check_turtle: bool = True,
) -> Tuple[int, List[Tuple[int, str]]]:
    """
    Check both JSON-LD and Turtle files for syntactic well-formedness.

    Args:
        paths: File path(s) or directory path(s) to check
        root_dir: Optional root directory for path normalization
        check_json: Whether to check JSON-LD files (default: True)
        check_turtle: Whether to check Turtle files (default: True)

    Returns:
        (return_code, results) tuple
    """
    all_results = []
    ret = 0

    if check_json:
        json_ret, json_results = check_json_wellformedness(paths, root_dir)
        ret |= json_ret
        all_results.extend(json_results)

    if check_turtle:
        turtle_ret, turtle_results = check_turtle_wellformedness(paths, root_dir)
        ret |= turtle_ret
        all_results.extend(turtle_results)

    return ret, all_results


# =============================================================================
# Legacy Aliases (backwards compatibility)
# =============================================================================

check_json_syntax = check_json_wellformedness
check_turtle_syntax = check_turtle_wellformedness
verify_json_syntax = check_json_wellformedness
verify_turtle_syntax = check_turtle_wellformedness
verify_all_syntax = check_all_wellformedness


# =============================================================================
# Self-Test
# =============================================================================


def _run_tests() -> bool:
    """Run self-tests for the module."""
    import tempfile

    print("Running syntax_validator self-tests...")
    all_passed = True

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Test 1: Valid JSON (single file)
        valid_json = tmppath / "valid.json"
        valid_json.write_text('{"key": "value"}')
        code, results = check_json_wellformedness(valid_json)
        if code != 0:
            print(f"FAIL: Valid JSON should pass: {results}")
            all_passed = False
        else:
            print("PASS: Valid JSON syntax")

        # Test 2: Invalid JSON
        invalid_json = tmppath / "invalid.json"
        invalid_json.write_text('{"key": "value",}')
        code, results = check_json_wellformedness(invalid_json)
        if code == 0:
            print("FAIL: Invalid JSON should fail")
            all_passed = False
        else:
            print("PASS: Invalid JSON detected")

        # Test 3: Valid Turtle (single file)
        valid_ttl = tmppath / "valid.ttl"
        valid_ttl.write_text(
            """@prefix ex: <http://example.org/> .
ex:subject a ex:Thing .
"""
        )
        code, results = check_turtle_wellformedness(valid_ttl)
        if code != 0:
            print(f"FAIL: Valid Turtle should pass: {results}")
            all_passed = False
        else:
            print("PASS: Valid Turtle syntax")

        # Test 4: Invalid Turtle
        invalid_ttl = tmppath / "invalid.ttl"
        invalid_ttl.write_text(
            """@prefix ex: <http://example.org/> .
ex:subject "unclosed string .
"""
        )
        code, results = check_turtle_wellformedness(invalid_ttl)
        if code == 0:
            print("FAIL: Invalid Turtle should fail")
            all_passed = False
        else:
            print("PASS: Invalid Turtle detected")

        # Test 5: Missing file
        code, results = check_json_wellformedness(tmppath / "nonexistent.json")
        if code == 0:
            print("FAIL: Missing file should fail")
            all_passed = False
        else:
            print("PASS: Missing file detected")

        # Test 6: Batch validation (directory)
        valid_dir = tmppath / "batch"
        valid_dir.mkdir()
        (valid_dir / "file1.json").write_text('{"a": 1}')
        (valid_dir / "file2.json").write_text('{"b": 2}')
        ret, results = check_json_wellformedness([str(valid_dir)])
        if ret != 0:
            print(f"FAIL: Batch validation should pass: {results}")
            all_passed = False
        else:
            print("PASS: Batch JSON validation")

        # Test 7: Multiple paths
        (valid_dir / "file3.ttl").write_text(
            "@prefix ex: <http://ex.org/> .\nex:a a ex:B .\n"
        )
        ret, results = check_all_wellformedness([str(valid_dir), str(valid_json)])
        if ret != 0:
            print(f"FAIL: Multi-path validation should pass: {results}")
            all_passed = False
        else:
            print("PASS: Multi-path validation")

    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")

    return all_passed


# =============================================================================
# CLI Entry Point
# =============================================================================


def main(args=None):
    """CLI entry point for syntax_validator."""
    parser = argparse.ArgumentParser(
        description="Check JSON-LD and Turtle files for syntactic well-formedness."
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to check")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument("--json", action="store_true", help="Check JSON-LD files only")
    parser.add_argument("--turtle", action="store_true", help="Check Turtle files only")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show errors")

    parsed_args = parser.parse_args(args)

    if parsed_args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    if not parsed_args.paths:
        parser.print_help()
        sys.exit(1)

    # Determine what to check
    do_json = not parsed_args.turtle or parsed_args.json
    do_turtle = not parsed_args.json or parsed_args.turtle

    # If neither specified explicitly, check both
    if not parsed_args.json and not parsed_args.turtle:
        do_json = True
        do_turtle = True

    ret, results = check_all_wellformedness(
        parsed_args.paths,
        root_dir=Path.cwd(),
        check_json=do_json,
        check_turtle=do_turtle,
    )

    # Print results
    for code, msg in results:
        if code == 0:
            if not parsed_args.quiet:
                sys.stdout.write(msg + "\n")
        else:
            sys.stderr.write(msg + "\n")

    sys.exit(ret)


if __name__ == "__main__":
    # Ensure UTF-8 output for emojis, etc.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
