#!/usr/bin/env python3
"""
Coherence Validator - SHACL Target Class vs OWL Class Validation

Validates that SHACL shape target classes are defined in the corresponding
OWL ontology. This ensures alignment between shapes and ontology definitions.

FEATURE SET:
============
1. validate_artifact_coherence - Validate SHACL targets match OWL definitions
2. extract_ontology_classes - Extract class definitions from OWL files
3. extract_shacl_classes - Extract target classes from SHACL files
4. get_base_ontology_classes - Load classes from base/imported ontologies

USAGE:
======
    from src.tools.validators.coherence_validator import (
        validate_artifact_coherence,
        extract_ontology_classes,
    )

    # Validate single domain
    code, msg = validate_artifact_coherence("manifest")

    # Extract classes from ontology
    classes = extract_ontology_classes("artifacts/manifest/manifest.owl.ttl")

STANDALONE TESTING:
==================
    python3 -m src.tools.validators.coherence_validator [--test] domain [owl_dir] [imports_dir]

DEPENDENCIES:
=============
- rdflib: For RDF graph handling

NOTES:
======
- Case-insensitive class matching (local names converted to lowercase)
- Base ontologies from imports/ are included in valid class set
"""

import argparse
import io
import sys
from pathlib import Path
from typing import Set, Tuple

from rdflib import OWL, RDF, RDFS, Graph, Namespace

from src.tools.core.iri_utils import get_local_name
from src.tools.core.logging import get_logger
from src.tools.core.result import ReturnCodes
from src.tools.utils.print_formatter import (
    format_artifact_coherence_result,
    normalize_path_for_display,
)
from src.tools.utils.registry_resolver import RegistryResolver

# Module logger
logger = get_logger(__name__)

# Define SHACL namespace
SH = Namespace("http://www.w3.org/ns/shacl#")


def extract_classes_from_graph(graph: Graph) -> Set[str]:
    """
    Extract local names of all classes (OWL and RDFS) from a graph.

    Args:
        graph: RDF graph to scan

    Returns:
        Set of lowercase class local names
    """
    classes = {
        get_local_name(str(cls), lowercase=True)
        for cls in graph.subjects(RDF.type, OWL.Class)
    }
    classes.update(
        {
            get_local_name(str(cls), lowercase=True)
            for cls in graph.subjects(RDF.type, RDFS.Class)
        }
    )
    return classes


def extract_shacl_classes_from_file(shacl_file: str) -> Set[str]:
    """
    Extract SHACL target classes from a single SHACL file.

    Args:
        shacl_file: Path to SHACL file

    Returns:
        Set of lowercase target class local names
    """
    shacl_classes = set()
    shacl_graph = Graph()
    shacl_graph.parse(shacl_file, format="turtle")

    for cls in shacl_graph.objects(None, SH.targetClass):
        local_name = get_local_name(str(cls), lowercase=True)
        shacl_classes.add(local_name)

    return shacl_classes


def extract_shacl_classes(directory: str) -> Set[str]:
    """
    Extract SHACL target classes from all SHACL files in a directory.

    .. deprecated::
        Use ``resolver.get_shacl_paths(domain)`` with
        ``extract_shacl_classes_from_file()`` instead.

    Args:
        directory: Path to directory containing SHACL files

    Returns:
        Set of lowercase target class local names
    """
    shacl_classes = set()
    for shacl_file in Path(directory).rglob("*shacl.ttl"):
        shacl_classes.update(extract_shacl_classes_from_file(str(shacl_file)))

    return shacl_classes


def extract_ontology_classes(ontology_file: str) -> Set[str]:
    """
    Extract class definitions from an ontology file.

    Args:
        ontology_file: Path to OWL ontology file

    Returns:
        Set of lowercase class local names
    """
    ontology_graph = Graph()
    ontology_graph.parse(ontology_file, format="turtle")

    return extract_classes_from_graph(ontology_graph)


def get_base_ontology_classes(resolver: RegistryResolver, root_dir: Path) -> Set[str]:
    """
    Load classes from base ontologies listed in imports/catalog-v001.xml.

    Args:
        resolver: RegistryResolver instance
        root_dir: Repository root directory

    Returns:
        Set of lowercase class local names from base ontologies
    """
    base_classes = set()
    for rel_path in resolver.get_base_ontology_paths():
        abs_path = resolver.to_absolute(rel_path)
        if not abs_path.exists():
            continue
        try:
            g = Graph()
            g.parse(str(abs_path), format="turtle")
            base_classes.update(extract_classes_from_graph(g))
        except Exception as e:
            logger.warning("Could not parse base ontology %s: %s", abs_path, e)
    return base_classes


def validate_artifact_coherence(
    domain: str,
    root_dir: Path = None,
    resolver: RegistryResolver = None,
    known_issues: Set[str] = None,
) -> Tuple[int, str]:
    """
    Validate that all target classes in SHACL shapes are defined in ontology.

    Args:
        domain: Ontology domain name (e.g., "hdmap", "manifest")
        root_dir: Repository root directory for path normalization
        resolver: Optional pre-configured RegistryResolver (with registered artifacts)
        known_issues: Optional set of lowercase class names to treat as known
            upstream issues.  These are excluded from the missing-class count
            and logged as warnings instead of errors.

    Returns:
        Tuple of (return_code, message) where return_code is 0 for success
    """
    root_dir = root_dir or Path.cwd()
    resolver = resolver if resolver else RegistryResolver(root_dir)

    ontology_rel = resolver.get_ontology_path(domain)
    shacl_rels = resolver.get_shacl_paths(domain)

    if not ontology_rel:
        message = (
            f"No ontology file found for '{domain}'. "
            "Target class validation cannot proceed."
        )
        return ReturnCodes.COHERENCE_ERROR, message

    if not shacl_rels:
        message = (
            f"No SHACL file found for '{domain}'. "
            "Target class validation cannot proceed."
        )
        return ReturnCodes.COHERENCE_ERROR, message

    ontology_file = resolver.to_absolute(ontology_rel)
    shacl_files = [resolver.to_absolute(p) for p in shacl_rels]

    if not ontology_file.exists():
        # Normalize paths for display
        ont_display = normalize_path_for_display(ontology_file, root_dir)
        message = (
            f"No ontology file found: {ont_display}. "
            "Target class validation cannot proceed."
        )
        return ReturnCodes.COHERENCE_ERROR, message

    missing_shacl = [p for p in shacl_files if not p.exists()]
    if missing_shacl:
        # Normalize paths for display
        missing_display = ", ".join(
            normalize_path_for_display(p, root_dir) for p in missing_shacl
        )
        message = (
            f"No SHACL file found: {missing_display}. "
            "Target class validation cannot proceed."
        )
        return ReturnCodes.COHERENCE_ERROR, message

    # Normalize paths for display (used in summary output)
    ont_display = normalize_path_for_display(ontology_file, root_dir)

    # Load base classes from imports catalog
    base_classes = get_base_ontology_classes(resolver, root_dir)

    # Extract classes from ontology
    ontology_classes = extract_ontology_classes(str(ontology_file))

    # Combine local classes with base classes
    valid_classes = ontology_classes.union(base_classes)

    # Extract SHACL target classes
    shacl_classes = set()
    for shacl_file in shacl_files:
        shacl_classes.update(extract_shacl_classes_from_file(str(shacl_file)))

    # Convert all to lowercase for case-insensitive matching
    valid_classes_lower = {cls.lower() for cls in valid_classes}
    shacl_classes_lower = {cls.lower() for cls in shacl_classes}

    matches = valid_classes_lower & shacl_classes_lower
    missing_classes = shacl_classes_lower - valid_classes_lower

    # Check against pure local classes for "extra" reporting
    local_classes_lower = {cls.lower() for cls in ontology_classes}
    extra_classes = local_classes_lower - shacl_classes_lower

    # Filter known upstream issues from missing classes
    known = known_issues or set()
    known_missing = missing_classes & known
    real_missing = missing_classes - known

    summary = format_artifact_coherence_result(
        ont_display,
        len(valid_classes),
        len(shacl_classes),
        matches,
        real_missing,
        extra_classes,
    )

    if known_missing:
        known_list = ", ".join(sorted(known_missing))
        summary += f"\n⚠️  Known upstream issue(s) excluded from failure: {known_list}"

    if real_missing:
        return ReturnCodes.COHERENCE_ERROR, summary

    return ReturnCodes.SUCCESS, summary


def _run_tests() -> bool:
    """Run self-tests for the module."""
    import tempfile

    print("Running coherence_validator self-tests...")
    all_passed = True

    # Test 1: get_local_name with hash (uses centralized iri_utils)
    result = get_local_name("http://example.org/ontology#MyClass", lowercase=True)
    if result != "myclass":
        print(f"FAIL: get_local_name hash - expected 'myclass', got '{result}'")
        all_passed = False
    else:
        print("PASS: get_local_name with hash")

    # Test 2: get_local_name with slash (uses centralized iri_utils)
    result = get_local_name("http://example.org/ontology/MyClass", lowercase=True)
    if result != "myclass":
        print(f"FAIL: get_local_name slash - expected 'myclass', got '{result}'")
        all_passed = False
    else:
        print("PASS: get_local_name with slash")

    # Test 3: Extract classes from graph
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        owl_file = tmppath / "test.owl.ttl"
        owl_file.write_text(
            """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <http://example.org/> .

:MyClass a owl:Class ;
    rdfs:label "My Class" .

:OtherClass a owl:Class .
"""
        )

        classes = extract_ontology_classes(str(owl_file))
        if "myclass" not in classes or "otherclass" not in classes:
            print(f"FAIL: extract_ontology_classes - got {classes}")
            all_passed = False
        else:
            print("PASS: extract_ontology_classes")

        # Test 4: Extract SHACL classes
        shacl_file = tmppath / "test.shacl.ttl"
        shacl_file.write_text(
            """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix : <http://example.org/> .

:MyClassShape a sh:NodeShape ;
    sh:targetClass :MyClass .
"""
        )

        shacl_classes = extract_shacl_classes_from_file(str(shacl_file))
        if "myclass" not in shacl_classes:
            print(f"FAIL: extract_shacl_classes - got {shacl_classes}")
            all_passed = False
        else:
            print("PASS: extract_shacl_classes")

    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")

    return all_passed


def main():
    """CLI entry point for coherence_validator."""
    parser = argparse.ArgumentParser(
        description="Validate SHACL target classes match OWL class definitions."
    )
    parser.add_argument("domain", nargs="?", help="Ontology domain name")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory (default: current directory)",
    )
    parser.add_argument("--test", action="store_true", help="Run self-tests")

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    if not args.domain:
        parser.print_help()
        sys.exit(1)

    root_dir = args.root.resolve()

    return_code, message = validate_artifact_coherence(args.domain, root_dir=root_dir)

    if return_code != 0:
        print(message, file=sys.stderr)
        sys.exit(return_code)
    else:
        print(message)
        sys.exit(0)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
