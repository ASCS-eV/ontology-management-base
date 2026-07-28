#!/usr/bin/env python3
"""
Unit tests for ``sh:severity sh:Warning`` handling.

pyshacl's default is to report *any* validation result as non-conformance, warnings
included, which makes ``sh:Warning`` unusable for "accepted but discouraged" constraints
such as deprecated enumeration values. ``ShaclValidator`` therefore passes
``allow_warnings`` and reports advisory results in their own section, kept out of the
``.expected`` snapshots that ``check-failing-tests`` compares byte for byte.
"""

from pathlib import Path

from rdflib import Graph, Namespace

from omb.validators.shacl.validator import ShaclValidator

EX = Namespace("http://example.org/")

# One shape, two constraints on the same property: a hard enumeration (Violation) and a
# deprecation check at warning severity — the encoding this support exists for.
SHAPES = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .

ex:ThingShape a sh:NodeShape ;
    sh:targetClass ex:Thing ;
    sh:property [
        sh:path ex:laneType ;
        sh:in ("driving" "sidewalk" "walking") ;
        sh:message "laneType must be a known lane type." ;
    ] ;
    sh:property [
        sh:path ex:laneType ;
        sh:not [ sh:in ("sidewalk") ] ;
        sh:severity sh:Warning ;
        sh:message "Lane type is deprecated; accepted for backward compatibility only." ;
    ] .
"""

DEPRECATED_ONLY = """
@prefix ex: <http://example.org/> .
ex:a a ex:Thing ; ex:laneType "sidewalk" .
"""

DEPRECATED_AND_UNKNOWN = """
@prefix ex: <http://example.org/> .
ex:a a ex:Thing ; ex:laneType "sidewalk" .
ex:b a ex:Thing ; ex:laneType "pavement" .
"""


def _make_validator(tmp: Path, allow_warnings: bool = True) -> ShaclValidator:
    (tmp / "docs").mkdir(parents=True, exist_ok=True)
    (tmp / "docs" / "registry.json").write_text('{"version":"1.0.0","ontologies":{}}')
    (tmp / "artifacts").mkdir(parents=True, exist_ok=True)
    (tmp / "artifacts" / "catalog-v001.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD Entity Resolution XML Catalog V1.0//EN"
  "http://www.oasis-open.org/committees/entity/release/1.0/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"></catalog>
"""
    )
    return ShaclValidator(
        tmp, inference_mode="none", verbose=False, allow_warnings=allow_warnings
    )


def _run(validator: ShaclValidator, data_ttl: str):
    data = Graph().parse(data=data_ttl, format="turtle")
    shapes = Graph().parse(data=SHAPES, format="turtle")
    return validator._run_validation(data, Graph(), shapes)


def test_warning_only_data_conforms_by_default(tmp_path: Path):
    """A warning alone must not fail validation, or deprecation cannot be modelled."""
    conforms, _text, report = _run(_make_validator(tmp_path), DEPRECATED_ONLY)
    assert conforms is True
    assert report is not None


def test_warning_only_data_fails_with_fail_on_warnings(tmp_path: Path):
    """``--fail-on-warnings`` restores pyshacl's strict behaviour."""
    conforms, _text, _report = _run(
        _make_validator(tmp_path, allow_warnings=False), DEPRECATED_ONLY
    )
    assert conforms is False


def test_violation_alongside_warning_still_fails(tmp_path: Path):
    """Allowing warnings must not mask a real violation on the same property."""
    conforms, _text, _report = _run(_make_validator(tmp_path), DEPRECATED_AND_UNKNOWN)
    assert conforms is False


def test_warnings_are_reported_but_excluded_from_the_snapshot(tmp_path: Path):
    """The advisory section carries the warning; the snapshot text carries only violations.

    This split is what keeps the recorded ``.expected`` files stable when a
    warning-severity constraint is added to a shape.
    """
    from omb.core.result import ValidationResult

    validator = _make_validator(tmp_path)
    conforms, text, report = _run(validator, DEPRECATED_AND_UNKNOWN)
    result = ValidationResult(
        conforms=conforms,
        return_code=0 if conforms else 210,
        report_text=text,
        report_graph=report,
        files_validated=["data.ttl"],
    )

    snapshot = validator.format_result(result)
    advisory = validator.format_advisory(result)

    assert "must be a known lane type" in snapshot
    assert "deprecated" not in snapshot.lower()

    assert "deprecated" in advisory.lower()
    assert "[Warning]" in advisory
    assert "do not fail validation" in advisory


def test_no_advisory_section_when_there_are_no_warnings(tmp_path: Path):
    from omb.core.result import ValidationResult

    validator = _make_validator(tmp_path)
    data = """
@prefix ex: <http://example.org/> .
ex:a a ex:Thing ; ex:laneType "driving" .
"""
    conforms, text, report = _run(validator, data)
    assert conforms is True

    result = ValidationResult(
        conforms=conforms,
        return_code=0,
        report_text=text,
        report_graph=report,
        files_validated=["data.ttl"],
    )
    assert validator.format_advisory(result) == ""
