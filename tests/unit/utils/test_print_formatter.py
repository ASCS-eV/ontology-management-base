#!/usr/bin/env python3
"""
Unit tests for omb.utils.print_formatter.
"""

from io import StringIO
from pathlib import Path

from rdflib import RDF, Graph, Literal, Namespace

from omb.utils import print_formatter


def test_normalize_path_for_display(temp_dir: Path):
    path = temp_dir / "nested" / "file.ttl"
    path.parent.mkdir(parents=True)
    path.write_text("")
    normalized = print_formatter.normalize_path_for_display(path, temp_dir)
    assert normalized == "nested/file.ttl"


def test_normalize_path_for_display_outside_root(temp_dir: Path, monkeypatch):
    """External paths render relative to CWD, not via a root_dir ``../`` traversal.

    Simulates a consumer whose CWD is its own repo root while OMB's data root
    (``root_dir``) lives elsewhere (e.g. an installed wheel's uv-cache dir).
    """
    outside_path = temp_dir.parent / "outside.ttl"
    outside_path.write_text("")
    monkeypatch.chdir(temp_dir.parent)
    normalized = print_formatter.normalize_path_for_display(outside_path, temp_dir)
    assert normalized == "outside.ttl"


def test_normalize_path_for_display_external_data_is_portable(tmp_path, monkeypatch):
    """A consumer data file under CWD renders as a clean repo-relative path even when
    root_dir is an unrelated, machine-specific install location.

    Reproduces the wheel/uv-cache case that made ``--data-paths`` reports non-portable:
    root_dir points at a packaged install dir, unrelated to the consumer's tree.
    """
    install_root = tmp_path / "uv-cache" / "site-packages" / "omb" / "data"
    install_root.mkdir(parents=True)
    repo = tmp_path / "consumer-repo"
    data = repo / "tests" / "omb" / "scenario" / "invalid" / "x.jsonld"
    data.parent.mkdir(parents=True)
    data.write_text("{}")

    monkeypatch.chdir(repo)
    normalized = print_formatter.normalize_path_for_display(data, install_root)
    assert normalized == "tests/omb/scenario/invalid/x.jsonld"


def test_normalize_text_scrubs_bnode():
    text = "N1234567890abcdef1234567890abcdef"
    normalized = print_formatter.normalize_text(text)
    assert "[BNODE]" in normalized or normalized == ""


def test_format_artifact_coherence_result_contains_header():
    out = print_formatter.format_artifact_coherence_result(
        "artifacts/demo/demo.owl.ttl",
        3,
        2,
        {"a"},
        set(),
        set(),
    )
    assert "VALIDATION SUMMARY" in out
    assert "Ontology File" in out


def test_format_data_conformance_result_success():
    buffer = StringIO()
    print_formatter.format_data_conformance_result(
        True, onto_files=["file.json"], report_graph=None, file=buffer
    )
    output = buffer.getvalue()
    assert "SHACL validation passed" in output


def test_format_data_conformance_result_with_errors():
    buffer = StringIO()
    SH = Namespace("http://www.w3.org/ns/shacl#")
    g = Graph()
    from rdflib import URIRef

    result = URIRef("urn:res1")
    g.add((result, RDF.type, SH.ValidationResult))
    g.add((result, SH.focusNode, URIRef("urn:node1")))
    g.add((result, SH.resultMessage, Literal("bad")))
    print_formatter.format_data_conformance_result(
        False, onto_files=["file.json"], report_graph=g, file=buffer
    )
    output = buffer.getvalue()
    assert "SHACL validation failed" in output
