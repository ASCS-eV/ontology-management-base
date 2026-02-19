#!/usr/bin/env python3
"""
File Collector - Centralized File Discovery and Write Utilities

FEATURE SET:
============
1. normalize_paths_to_list - Convert single path or list to list of strings
2. collect_files_by_extension - Generic extension-based file collection
3. collect_turtle_files - Collect all .ttl files from paths
4. collect_jsonld_files - Collect all .json/.jsonld files from paths
5. collect_ontology_bundles - Discover complete ontology bundles
6. collect_files_by_pattern - Glob pattern-based collection
7. collect_ontology_files - Get {ontology, shacl, context} paths for a domain
8. collect_test_files - Collect test files from valid/invalid subdirs
9. write_if_changed - Write file only if content differs (with LF normalization)
10. discover_data_hierarchy - Auto-detect top-level files vs fixtures

PATH INPUT:
==========
All collection functions accept flexible path input (PathsInput type):
- Single file: "data/file.json" or Path("data/file.json")
- Single directory: "artifacts/" or Path("artifacts/")
- List of paths: ["data/", "examples/", "file.json"]

USAGE:
======
    from src.tools.utils.file_collector import (
        normalize_paths_to_list,
        collect_jsonld_files,
        collect_turtle_files,
    )

    # Single file or directory
    files = collect_jsonld_files("data/instance.json")
    files = collect_turtle_files("artifacts/")

    # Multiple paths
    files = collect_jsonld_files(["data/", "examples/"])

STANDALONE TESTING:
==================
    python3 -m src.tools.utils.file_collector [--test] [--verbose] [paths...]

DEPENDENCIES:
=============
- pathlib: For path operations (stdlib)
- No external dependencies - this module is intentionally pure

NOTES:
======
- This module has NO internal src.tools imports to avoid circular dependencies
- All file discovery logic should be centralized here
- Other modules should delegate file discovery to these functions
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

# Type alias for flexible path input (single or multiple)
PathsInput = Union[str, Path, List[Union[str, Path]]]


def normalize_paths_to_list(paths: PathsInput) -> List[str]:
    """
    Normalize path input to a list of string paths.

    Accepts a single path (str or Path) or a list of paths, and returns
    a list of string paths. This is useful for functions that accept
    flexible input but internally need a list.

    Args:
        paths: Single path or list of paths

    Returns:
        List of string paths

    Examples:
        >>> normalize_paths_to_list("data/file.json")
        ['data/file.json']
        >>> normalize_paths_to_list(Path("artifacts/"))
        ['artifacts']
        >>> normalize_paths_to_list(["data/", "examples/"])
        ['data/', 'examples/']
    """
    if isinstance(paths, (str, Path)):
        return [str(paths)]
    return [str(p) for p in paths]


def collect_files_by_extension(
    paths: PathsInput,
    extensions: Union[str, Set[str]],
    warn_on_invalid: bool = True,
    return_pathlib: bool = False,
    sort_and_deduplicate: bool = False,
) -> List[Union[str, Path]]:
    """
    Collect all files with specified extensions from the given paths.

    This function walks through directories recursively and collects files
    matching the specified extensions. It can handle a single file/directory
    or a list of files/directories.

    Args:
        paths: Single path or list of file/directory paths to search
        extensions: File extension(s) to collect (e.g., ".ttl" or {".json", ".jsonld"})
                    Extensions should include the dot prefix
        warn_on_invalid: If True, write warnings to stderr for invalid paths
        return_pathlib: If True, return Path objects; if False, return strings
        sort_and_deduplicate: If True, sort and remove duplicates from results

    Returns:
        List of file paths matching the specified extensions

    Examples:
        # Single file
        files = collect_files_by_extension("data/file.ttl", ".ttl")

        # Single directory
        files = collect_files_by_extension("artifacts/", ".ttl")

        # Multiple paths
        files = collect_files_by_extension(
            ["data/", "examples/"],
            {".json", ".jsonld"},
            return_pathlib=True,
            sort_and_deduplicate=True
        )
    """
    # Normalize paths to list
    path_list = normalize_paths_to_list(paths)

    # Normalize extensions to a set
    if isinstance(extensions, str):
        ext_set = {extensions}
    else:
        ext_set = set(extensions)

    # Ensure all extensions start with a dot
    ext_set = {ext if ext.startswith(".") else f".{ext}" for ext in ext_set}

    files = []

    for path_input in path_list:
        path = Path(path_input).resolve()

        if path.is_file():
            # Check if file has the right extension
            if path.suffix in ext_set:
                files.append(path if return_pathlib else str(path))
            elif warn_on_invalid:
                sys.stderr.write(
                    f"Warning: Ignoring file with wrong extension: {path}\n"
                )
        elif path.is_dir():
            # Walk directory recursively
            for file_path in path.rglob("*"):
                if file_path.is_file() and file_path.suffix in ext_set:
                    files.append(file_path if return_pathlib else str(file_path))
        elif warn_on_invalid:
            sys.stderr.write(
                f"Warning: Ignoring invalid path or unsupported file: {path}\n"
            )

    # Sort and deduplicate if requested
    if sort_and_deduplicate:
        files = sorted(set(files))

    return files


def collect_turtle_files(
    paths: PathsInput,
    warn_on_invalid: bool = True,
    return_pathlib: bool = False,
) -> List[Union[str, Path]]:
    """
    Collect all Turtle (.ttl) files from the given paths.

    Args:
        paths: Single path or list of file/directory paths to search
        warn_on_invalid: If True, write warnings to stderr for invalid paths
        return_pathlib: If True, return Path objects; if False, return strings

    Returns:
        List of Turtle file paths
    """
    return collect_files_by_extension(
        paths, ".ttl", warn_on_invalid=warn_on_invalid, return_pathlib=return_pathlib
    )


def collect_jsonld_files(
    paths: PathsInput,
    warn_on_invalid: bool = True,
    return_pathlib: bool = False,
    sort_and_deduplicate: bool = False,
) -> List[Union[str, Path]]:
    """
    Collect all JSON-LD (.json, .jsonld) files from the given paths.

    Args:
        paths: Single path or list of file/directory paths to search
        warn_on_invalid: If True, write warnings to stderr for invalid paths
        return_pathlib: If True, return Path objects; if False, return strings
        sort_and_deduplicate: If True, sort and remove duplicates

    Returns:
        List of JSON-LD file paths
    """
    return collect_files_by_extension(
        paths,
        {".json", ".jsonld"},
        warn_on_invalid=warn_on_invalid,
        return_pathlib=return_pathlib,
        sort_and_deduplicate=sort_and_deduplicate,
    )


def collect_files_by_pattern(
    paths: PathsInput,
    pattern: str,
    return_pathlib: bool = False,
) -> List[Union[str, Path]]:
    """
    Generic pattern-based file collection using glob patterns.

    Args:
        paths: Single path or list of directory paths to search
        pattern: Glob pattern to match (e.g., "*.shacl.ttl", "**/*.json")
        return_pathlib: If True, return Path objects; if False, return strings

    Returns:
        List of matching file paths
    """
    # Normalize paths to list
    path_list = normalize_paths_to_list(paths)
    files = []

    for path_input in path_list:
        path = Path(path_input).resolve()

        if path.is_dir():
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    files.append(file_path if return_pathlib else str(file_path))
        elif path.is_file() and path.match(pattern):
            files.append(path if return_pathlib else str(path))

    return sorted(set(files))


def collect_ontology_files(domain_dir: Path) -> Dict[str, Optional[Path]]:
    """
    Discover ontology files for a domain directory.

    Returns {ontology, shacl, context} paths for a domain following the
    standard naming convention: {domain}.owl.ttl, {domain}.shacl.ttl,
    {domain}.context.jsonld

    Args:
        domain_dir: Path to domain directory (e.g., artifacts/manifest/)

    Returns:
        Dictionary with keys: ontology, shacl (list), context
        Values are Path objects or None if not found
    """
    domain = domain_dir.name

    # Standard file patterns
    ontology_file = domain_dir / f"{domain}.owl.ttl"
    context_file = domain_dir / f"{domain}.context.jsonld"

    # SHACL files can be multiple: domain.shacl.ttl and domain.*.shacl.ttl
    shacl_files = sorted(domain_dir.glob("*.shacl.ttl"))

    return {
        "ontology": ontology_file if ontology_file.exists() else None,
        "shacl": shacl_files if shacl_files else None,
        "context": context_file if context_file.exists() else None,
    }


def collect_test_files(
    test_dir: Path,
    valid: bool = True,
    extensions: Set[str] = None,
) -> List[Path]:
    """
    Collect test files from valid/ or invalid/ subdirectories.

    Args:
        test_dir: Path to test domain directory (e.g., tests/data/manifest/)
        valid: If True, collect from valid/, otherwise from invalid/
        extensions: File extensions to collect (default: {".json", ".jsonld"})

    Returns:
        List of test file paths
    """
    if extensions is None:
        extensions = {".json", ".jsonld"}

    subdir = "valid" if valid else "invalid"
    target_dir = test_dir / subdir

    if not target_dir.exists():
        return []

    return collect_files_by_extension(
        [target_dir],
        extensions,
        warn_on_invalid=False,
        return_pathlib=True,
        sort_and_deduplicate=True,
    )


def collect_ontology_bundles(
    base_dir: Path, tests_dir: Optional[Path] = None
) -> Dict[str, Dict[str, Union[Path, List[Path], None]]]:
    """
    Discover ontology bundles (Ontology, SHACL, Context, Tests) in a directory.

    Assumes the standard project structure:
      {base_dir}/{domain}/{domain}.owl.ttl
      {base_dir}/{domain}/*.shacl.ttl
      {base_dir}/{domain}/{domain}.context.jsonld
      {tests_dir}/{domain}/valid/*_instance.json (optional)

    Args:
        base_dir: Directory containing domain subdirectories (e.g., artifacts/ or imports/)
        tests_dir: Optional directory containing test data (e.g., tests/data/)

    Returns:
        Dictionary mapping domain names to a bundle of absolute Path objects:
        {
            "domain": {
                "ontology": Path(...),
                "shacl": [Path(...), ...],
                "jsonld": Path(...) or None,
                "properties": Path(...) or None,
                "instance": Path(...) or None
            }
        }
    """
    bundles = {}

    if not base_dir.exists():
        sys.stderr.write(f"Warning: Directory not found: {base_dir}\n")
        return bundles

    # Iterate over domain directories
    for ont_dir in sorted(base_dir.iterdir()):
        if not ont_dir.is_dir():
            continue

        domain = ont_dir.name

        # 1. Ontology File: {domain}.owl.ttl
        owl_file = ont_dir / f"{domain}.owl.ttl"
        if not owl_file.exists():
            continue

        # 2. SHACL Files: *.shacl.ttl
        shacl_files = sorted(ont_dir.glob("*.shacl.ttl"))

        # 3. JSON-LD Context
        jsonld_file = ont_dir / f"{domain}.context.jsonld"

        # 4. Properties Documentation
        properties_file = ont_dir / "PROPERTIES.md"

        # 5. Instance File (from tests directory if provided)
        instance_file = None
        if tests_dir and tests_dir.exists():
            valid_dir = tests_dir / domain / "valid"
            if valid_dir.exists():
                # Look for standard instance patterns
                for pattern in [f"{domain}_instance.json", "*_instance.json"]:
                    matches = list(valid_dir.glob(pattern))
                    if matches:
                        instance_file = matches[0]
                        break

        bundles[domain] = {
            "ontology": owl_file.resolve(),
            "shacl": [f.resolve() for f in shacl_files] if shacl_files else None,
            "jsonld": jsonld_file.resolve() if jsonld_file.exists() else None,
            "properties": (
                properties_file.resolve() if properties_file.exists() else None
            ),
            "instance": instance_file.resolve() if instance_file else None,
        }

    return bundles


def write_if_changed(path: Path, content: str) -> bool:
    """
    Write content to file only if it differs from existing content.

    Uses LF line endings for cross-platform consistency.
    Normalizes line endings when comparing to avoid false positives.

    Args:
        path: Target file path
        content: New content to write

    Returns:
        True if file was written, False if unchanged
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize to LF for comparison
    def normalize(s: str) -> str:
        return s.replace("\r\n", "\n").replace("\r", "\n")

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if normalize(existing) == normalize(content):
            return False

    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return True


def extract_jsonld_iris(file_path: Path) -> tuple:
    """
    Extract root @id and all referenced IRIs from a JSON-LD file.

    Args:
        file_path: Path to JSON-LD file

    Returns:
        Tuple of (root_id, referenced_iris) where:
        - root_id: The @id value of the document, or None
        - referenced_iris: Set of IRIs referenced in nested objects
    """
    import json as _json

    try:
        with file_path.open("r", encoding="utf-8") as f:
            doc = _json.load(f)
    except Exception:
        return None, set()

    root_id = doc.get("@id") or doc.get("id")
    referenced: Set[str] = set()

    def extract_from_value(value, depth: int = 0):
        """Recursively extract @id values from nested structures."""
        if isinstance(value, dict):
            obj_id = value.get("@id") or value.get("id")
            if obj_id and depth > 0 and obj_id != root_id:
                # Only add if it looks like an IRI (not a blank node)
                if isinstance(obj_id, str) and not obj_id.startswith("_:"):
                    referenced.add(obj_id)
            for v in value.values():
                extract_from_value(v, depth + 1)
        elif isinstance(value, list):
            for item in value:
                extract_from_value(item, depth + 1)

    extract_from_value(doc)
    return root_id, referenced


def discover_data_hierarchy(
    paths: List[Union[str, Path]],
) -> tuple:
    """
    Discover top-level files and fixture mappings from paths.

    This function implements smart path expansion:
    - FILE: Added to validate list, parent directory scanned for fixtures
    - DIRECTORY: Scanned recursively, auto-detects top-level vs fixtures

    Top-level files: Files whose @id is NOT referenced by any other file.
    Fixtures: Files whose @id IS referenced by another file.

    Args:
        paths: List of files or directories to process

    Returns:
        Tuple of (files_to_validate, iri_to_file_map)
        - files_to_validate: List of Path objects to validate
        - iri_to_file_map: Dict mapping IRIs to file paths (for fixture resolution)
    """
    explicit_files: List[Path] = []
    scan_dirs: Set[Path] = set()

    # Expand paths: files → validate + scan parent, dirs → scan
    for p in paths:
        p = Path(p).resolve()
        if p.is_file():
            explicit_files.append(p)
            scan_dirs.add(p.parent)
        elif p.is_dir():
            scan_dirs.add(p)

    # Collect all JSON-LD files from directories
    all_files: List[Path] = []
    if scan_dirs:
        all_files = collect_jsonld_files(
            list(scan_dirs), return_pathlib=True, sort_and_deduplicate=True
        )

    # Single pass: build IRI→file mapping and collect all referenced IRIs
    iri_to_file: Dict[str, Path] = {}
    referenced_iris: Set[str] = set()
    file_ids: Dict[Path, Optional[str]] = {}

    for f in all_files:
        root_id, refs = extract_jsonld_iris(f)
        file_ids[f] = root_id
        if root_id:
            iri_to_file[root_id] = f
        referenced_iris.update(refs)

    # Top-level = explicit files + files not referenced by others
    top_level: Set[Path] = set(explicit_files)
    for f, fid in file_ids.items():
        if fid and fid not in referenced_iris:
            top_level.add(f)

    return sorted(top_level), iri_to_file


def _run_tests() -> bool:
    """Run self-tests for the module."""
    import tempfile

    print("Running file_collector self-tests...")
    all_passed = True

    # Test 1: collect_files_by_extension with empty list
    result = collect_files_by_extension([], ".ttl")
    if result != []:
        print("FAIL: Empty input should return empty list")
        all_passed = False
    else:
        print("PASS: Empty input handling")

    # Test 2: Create temp files and collect them
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        (tmppath / "test1.json").write_text("{}")
        (tmppath / "test2.jsonld").write_text("{}")
        (tmppath / "test3.ttl").write_text("")
        (tmppath / "subdir").mkdir()
        (tmppath / "subdir" / "nested.json").write_text("{}")

        # Test JSON-LD collection
        jsonld_files = collect_jsonld_files([tmppath], return_pathlib=True)
        if len(jsonld_files) != 3:
            print(f"FAIL: Expected 3 JSON-LD files, got {len(jsonld_files)}")
            all_passed = False
        else:
            print("PASS: JSON-LD file collection")

        # Test Turtle collection
        turtle_files = collect_turtle_files([tmppath], return_pathlib=True)
        if len(turtle_files) != 1:
            print(f"FAIL: Expected 1 Turtle file, got {len(turtle_files)}")
            all_passed = False
        else:
            print("PASS: Turtle file collection")

        # Test sort and deduplicate
        jsonld_sorted = collect_jsonld_files(
            [tmppath, tmppath],
            return_pathlib=True,
            sort_and_deduplicate=True,
        )
        if len(jsonld_sorted) != 3:
            print(f"FAIL: Deduplication failed, got {len(jsonld_sorted)}")
            all_passed = False
        else:
            print("PASS: Sort and deduplicate")

        # Test pattern-based collection
        pattern_files = collect_files_by_pattern([tmppath], "**/*.json")
        if len(pattern_files) != 2:
            print(f"FAIL: Expected 2 .json files, got {len(pattern_files)}")
            all_passed = False
        else:
            print("PASS: Pattern-based collection")

    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")

    return all_passed


def main():
    """CLI entry point for file_collector."""
    parser = argparse.ArgumentParser(
        description="Collect files by extension from paths"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to search (files or directories)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--extension",
        "-e",
        default=".json",
        help="Extension to collect (default: .json)",
    )
    parser.add_argument(
        "--jsonld",
        action="store_true",
        help="Collect JSON-LD files (.json, .jsonld)",
    )
    parser.add_argument(
        "--turtle",
        action="store_true",
        help="Collect Turtle files (.ttl)",
    )

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    if not args.paths:
        parser.print_help()
        sys.exit(1)

    # Collect files based on options
    if args.jsonld:
        files = collect_jsonld_files(args.paths, sort_and_deduplicate=True)
    elif args.turtle:
        files = collect_turtle_files(args.paths)
    else:
        files = collect_files_by_extension(
            args.paths,
            args.extension,
            sort_and_deduplicate=True,
        )

    # Print results
    if args.verbose:
        print(f"Found {len(files)} file(s):")

    for f in files:
        print(f)


if __name__ == "__main__":
    main()
