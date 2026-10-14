#!/usr/bin/env python3
"""
Validation result types and return codes.

FEATURE SET:
============
1. ReturnCodes enum - Standardized exit codes for all validation operations
2. ValidationResult dataclass - Structured validation outcome with metadata
3. Violation dataclass - One located SHACL constraint violation
4. Helper functions for creating common result types

USAGE:
======
    from omb.core.result import ValidationResult, ReturnCodes

    # Create a successful result
    result = ValidationResult(
        conforms=True,
        return_code=ReturnCodes.SUCCESS,
        report_text="All validations passed"
    )

    # Check result
    if result.conforms:
        print("Validation passed!")
    else:
        print(f"Error: {result.report_text}")
        sys.exit(result.return_code)

STANDALONE TESTING:
==================
    python3 -m omb.core.result [--test]

DEPENDENCIES:
=============
- rdflib: For Graph type annotation

NOTES:
======
- Return codes follow Unix conventions (0 = success, non-zero = error)
- Codes are grouped by category (syntax: 10x, coherence: 20x, etc.)
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional

from rdflib import Graph


class ReturnCodes(IntEnum):
    """
    Standardized return codes for validation operations.

    Grouped by category:
    - 0: Success
    - 1: General error
    - 10-10x: Syntax errors
    - 20x: Coherence/consistency errors
    - 21x: Conformance/SHACL errors
    - 99: System/dependency errors
    - 100: Skipped
    """

    SUCCESS = 0
    GENERAL_ERROR = 1

    # Syntax validation (10x)
    SYNTAX_ERROR = 10
    JSON_SYNTAX_ERROR = 101
    TURTLE_SYNTAX_ERROR = 102

    # Coherence validation (20x)
    COHERENCE_ERROR = 200
    MISSING_TARGET_CLASS = 201

    # Conformance validation (21x)
    CONFORMANCE_ERROR = 210
    SHACL_VIOLATION = 211

    # System errors (99)
    MISSING_DEPENDENCY = 99

    # Skip conditions
    SKIPPED = 100


@dataclass(frozen=True, order=True)
class Violation:
    """One distinct SHACL constraint violation, located in the validated data.

    pySHACL reports a failure inside a nested shape as a chain of results joined
    by ``sh:detail``; a violation is the end of such a chain, the constraint that
    actually failed. Instances sort by file, then path, then message.

    Attributes:
        file: The input file the violation was found in, as displayed in
            ``files_validated``. When several files are validated together it is
            the one describing ``focus_node``, names joined with ", " when more
            than one does, and empty for a node none of them holds, such as one
            loaded from a resolved fixture.
        path: Property path from ``focus_node`` to the failing value, one local
            name per step joined with "/", in SHACL path notation for complex
            steps (``^p`` inverse, ``(a|b)`` alternative, ``p*``, ``p+``,
            ``p?``). Empty when the constraint applies to ``focus_node`` itself.
        message: The failed constraint's message, with long node renderings
            shortened to ``[ ... ]`` and blank node identifiers scrubbed.
        component: Local name of the SHACL constraint component, such as
            ``MinCountConstraintComponent``.
        focus_node: Where ``path`` starts: the focus node of the top-level
            result, normally the validated document's subject. An IRI verbatim,
            a blank node as ``[BNODE]``.
        value: The offending value, or empty when the constraint has none (a
            missing property). A blank node is ``[BNODE]``.
        source_shape: IRI of the shape declaring the failed constraint, or empty
            when that shape is a blank node.
        severity: Severity of the top-level result, the one that decides
            conformance: ``Violation``, ``Warning`` or ``Info``.
    """

    file: str
    path: str
    message: str
    component: str
    focus_node: str
    value: str
    source_shape: str
    severity: str

    def __str__(self) -> str:
        """``message (at path)``, prefixed with the file when one is known."""
        text = f"{self.message} (at {self.path})" if self.path else self.message
        return f"{self.file}: {text}" if self.file else text


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    This dataclass provides a structured way to represent validation outcomes,
    including both success/failure status and detailed metadata about the
    validation run.

    Attributes:
        conforms: Whether the validation passed (True) or failed (False)
        return_code: Exit code for CLI usage (0 = success)
        report_text: Human-readable report or error message
        report_graph: Optional RDF graph with SHACL validation report
        files_validated: List of files that were validated
        triples_count: Total number of RDF triples processed
        inferred_count: Number of triples added by inference
        duration_seconds: Time taken for validation
        errors: Why validation could not reach a verdict: no input, no SHACL
            shape covering an input, an unresolved IRI or ``@type`` in strict
            mode, a missing dependency. Empty when a verdict was reached. A
            constraint violation is a verdict (``conforms=False``), reported in
            ``violations``, never here.
        warnings: List of warning messages
        shapes_loaded: Number of node/property shapes discovered by pySHACL (including implicit shapes)
        target_types: Sorted @type IRIs found in validated data
        types_routed: Target types that resolve to a domain/imported namespace
        types_unrouted: Target types that resolve to neither
        per_type_shape_count: Shapes targeting each found @type IRI
        violations: One :class:`Violation` per distinct SHACL constraint
            violation that counts against conformance, sorted. Advisory
            (``sh:Warning``/``sh:Info``) results are not included.
    """

    conforms: bool
    return_code: int
    report_text: str
    report_graph: Optional[Graph] = None
    files_validated: List[str] = field(default_factory=list)
    triples_count: int = 0
    inferred_count: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    shapes_loaded: int = 0
    target_types: List[str] = field(default_factory=list)
    types_routed: List[str] = field(default_factory=list)
    types_unrouted: List[str] = field(default_factory=list)
    per_type_shape_count: Dict[str, int] = field(default_factory=dict)
    violations: List[Violation] = field(default_factory=list)

    @classmethod
    def success(
        cls, report_text: str = "Validation passed", files: List[str] = None
    ) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(
            conforms=True,
            return_code=ReturnCodes.SUCCESS,
            report_text=report_text,
            files_validated=files or [],
        )

    @classmethod
    def error(
        cls,
        return_code: int,
        report_text: str,
        files: List[str] = None,
        errors: List[str] = None,
    ) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(
            conforms=False,
            return_code=return_code,
            report_text=report_text,
            files_validated=files or [],
            errors=errors or [],
        )

    @classmethod
    def skipped(cls, reason: str, files: List[str] = None) -> "ValidationResult":
        """Create a skipped validation result."""
        return cls(
            conforms=True,  # Skipped is not a failure
            return_code=ReturnCodes.SKIPPED,
            report_text=reason,
            files_validated=files or [],
            warnings=[reason],
        )

    def is_success(self) -> bool:
        """Check if this is a successful result."""
        return self.conforms and self.return_code == ReturnCodes.SUCCESS

    def is_error(self) -> bool:
        """Check if this is an error result."""
        return not self.conforms or self.return_code not in (
            ReturnCodes.SUCCESS,
            ReturnCodes.SKIPPED,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Show result types")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        print("Running self-tests...")

        # Test ReturnCodes
        assert ReturnCodes.SUCCESS == 0
        assert ReturnCodes.SYNTAX_ERROR == 10
        assert ReturnCodes.CONFORMANCE_ERROR == 210

        # Test ValidationResult
        success = ValidationResult.success("Test passed", ["file1.json"])
        assert success.conforms is True
        assert success.return_code == 0
        assert success.is_success() is True
        assert success.is_error() is False

        error = ValidationResult.error(ReturnCodes.SYNTAX_ERROR, "Parse error")
        assert error.conforms is False
        assert error.return_code == ReturnCodes.SYNTAX_ERROR
        assert error.is_success() is False
        assert error.is_error() is True

        skipped = ValidationResult.skipped("No files found")
        assert skipped.conforms is True
        assert skipped.return_code == ReturnCodes.SKIPPED
        assert skipped.is_success() is False
        assert skipped.is_error() is False

        print("All tests passed!")
    else:
        print("ReturnCodes:")
        for code in ReturnCodes:
            print(f"  {code.name}: {code.value}")
