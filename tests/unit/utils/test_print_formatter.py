#!/usr/bin/env python3
"""
Unit tests for omb.utils.print_formatter.
"""

import json
from io import StringIO
from pathlib import Path

from rdflib import RDF, Graph, Literal, Namespace

from omb.core.result import Violation
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


def test_clean_sh_in_message_sorted_values():
    """pySHACL lists sh:in values in set order; the report must not depend on it."""
    one = "Value <urn:x> not in list ['ex:b', 'ex:c', 'ex:a']"
    other = "Value <urn:x> not in list ['ex:c', 'ex:a', 'ex:b']"
    assert print_formatter._clean(one) == print_formatter._clean(other)
    assert print_formatter._clean(one).endswith("['ex:a', 'ex:b', 'ex:c']")


def test_clean_custom_message_mentioning_list_unchanged():
    message = "The role is not in list [see the ENVITED-X roles]"
    assert print_formatter._clean(message) == message


def test_clean_truncated_node_rendering_collapsed():
    """Where pySHACL cuts a rendering off depends on hashing; the report must not."""
    deep = "<http://recursion.too.deep>"
    one = (
        f'Node [ ex:p [ ex:q {deep} ] ; ex:r "a ] b" ] must conform to [ sh:path ex:p ]'
    )
    other = f'Node [ ex:p [ ex:q [ ex:s {deep} ] ] ; ex:r "a ] b" ] must conform to [ sh:path ex:p ]'
    assert print_formatter._clean(one) == print_formatter._clean(other)
    assert (
        print_formatter._clean(one) == "Node [ ... ] must conform to [ sh:path ex:p ]"
    )


def test_clean_complete_node_rendering_kept():
    message = 'Node [ ex:p "x" ; ex:q [ ex:r ex:s ] ] must not conform to ex:Shape'
    assert print_formatter._clean(message) == message


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


PREFIXES = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <https://example.org/v1/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

#: A road whose lanes must each carry an integer width.
LANE_SHAPES = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:lane ; sh:node ex:LaneShape ] .
ex:LaneShape a sh:NodeShape ;
    sh:property [ sh:path ex:width ; sh:datatype xsd:integer ] .
"""


def _report(shapes: str, data: str, data_format: str = "turtle", **options):
    """Validates ``data`` against ``shapes`` with pySHACL; returns (conforms, report)."""
    from pyshacl import validate

    shapes_graph = Graph().parse(data=PREFIXES + shapes, format="turtle")
    if data_format == "turtle":
        data = PREFIXES + data
    data_graph = Graph().parse(data=data, format=data_format)
    conforms, report_graph, _ = validate(
        data_graph, shacl_graph=shapes_graph, **options
    )
    return conforms, report_graph


def _jsonld(**properties) -> str:
    """A JSON-LD road document; nested objects become blank nodes."""
    document = {
        "@context": {"ex": "https://example.org/v1/"},
        "@id": "ex:road",
        "@type": "ex:Road",
    }
    document.update({f"ex:{name}": value for name, value in properties.items()})
    return json.dumps(document)


def test_extract_violations_locates_nested_violation_from_document_root():
    """Only the failed constraint is reported, located from the document's subject."""
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:network ; sh:node ex:NetworkShape ] .
ex:NetworkShape a sh:NodeShape ;
    sh:property [ sh:path ex:lane ; sh:node ex:LaneShape ] .
ex:LaneShape a sh:NodeShape ;
    sh:property [ sh:path ex:width ; sh:datatype xsd:integer ] .
"""
    _, report = _report(
        shapes, 'ex:road a ex:Road ; ex:network [ ex:lane [ ex:width "wide" ] ] .'
    )

    violations = print_formatter.extract_violations(
        report, file_of=lambda node: "road.ttl"
    )

    assert violations == [
        Violation(
            file="road.ttl",
            path="network/lane/width",
            message="Value is not Literal with datatype xsd:integer",
            component="DatatypeConstraintComponent",
            focus_node="https://example.org/v1/road",
            value="wide",
            source_shape="",
            severity="Violation",
        )
    ]
    assert str(violations[0]) == (
        "road.ttl: Value is not Literal with datatype xsd:integer "
        "(at network/lane/width)"
    )


def test_extract_violations_keeps_distinct_blank_nodes_apart():
    """Two nested objects failing the same way are two violations, not one."""
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:leftLane ; sh:node ex:LaneShape ] ;
    sh:property [ sh:path ex:rightLane ; sh:node ex:LaneShape ] .
ex:LaneShape a sh:NodeShape ;
    sh:property [ sh:path ex:width ; sh:datatype xsd:integer ] .
"""
    data = _jsonld(leftLane={"ex:width": "wide"}, rightLane={"ex:width": "wide"})
    _, report = _report(shapes, data, data_format="json-ld")

    violations = print_formatter.extract_violations(report)

    assert [v.path for v in violations] == ["leftLane/width", "rightLane/width"]


def test_extract_violations_counts_identical_blank_nodes_on_one_path():
    data = _jsonld(lane=[{"ex:width": "wide"}, {"ex:width": "wide"}])
    _, report = _report(LANE_SHAPES, data, data_format="json-ld")

    violations = print_formatter.extract_violations(report)

    assert [v.path for v in violations] == ["lane/width", "lane/width"]


def test_extract_violations_reports_standalone_and_nested_route_once():
    """A nested shape with its own target is validated twice; that is one violation.

    It is kept at the longer path, the one rooted at the validated document.
    """
    shapes = LANE_SHAPES + "ex:LaneShape sh:targetClass ex:Lane ."
    data = 'ex:road a ex:Road ; ex:lane ex:l1 . ex:l1 a ex:Lane ; ex:width "wide" .'
    _, report = _report(shapes, data)

    violations = print_formatter.extract_violations(report)

    assert [(v.focus_node, v.path) for v in violations] == [
        ("https://example.org/v1/road", "lane/width")
    ]


def test_extract_violations_resolves_equally_long_paths_deterministically():
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:beta ; sh:node ex:LaneShape ] ;
    sh:property [ sh:path ex:alpha ; sh:node ex:LaneShape ] .
ex:LaneShape a sh:NodeShape ;
    sh:property [ sh:path ex:width ; sh:datatype xsd:integer ] .
"""
    data = (
        'ex:road a ex:Road ; ex:alpha ex:l1 ; ex:beta ex:l1 . ex:l1 ex:width "wide" .'
    )
    _, report = _report(shapes, data)

    assert [v.path for v in print_formatter.extract_violations(report)] == [
        "alpha/width"
    ]


def test_extract_violations_violation_reaching_a_warning_constraint_counts():
    """Severity comes from the top-level result, which alone decides conformance."""
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:lane ; sh:node ex:LaneShape ] .
ex:LaneShape a sh:NodeShape ;
    sh:property [ sh:path ex:width ; sh:minCount 1 ; sh:severity sh:Warning ] .
"""
    conforms, report = _report(shapes, 'ex:road a ex:Road ; ex:lane [ ex:id "a" ] .')

    assert conforms is False
    violations = print_formatter.extract_violations(report)
    assert [(v.path, v.severity) for v in violations] == [("lane/width", "Violation")]
    assert print_formatter.extract_violations(report, advisory=True) == []


def test_extract_violations_warning_reaching_a_violation_constraint_is_advisory():
    """The hdmap revision checks: a Warning shape whose nested constraints say Violation."""
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ; sh:severity sh:Warning ;
    sh:node ex:RevisionShape .
ex:RevisionShape a sh:NodeShape ;
    sh:or ( [ sh:property [ sh:path ex:version ; sh:hasValue "1.5" ] ]
            [ sh:property [ sh:path ex:type ; sh:in ( "town" ) ] ] ) .
"""
    data = 'ex:road a ex:Road ; ex:version "1.4" ; ex:type "townExpressway" .'
    conforms, report = _report(shapes, data, allow_warnings=True)

    assert conforms is True
    assert print_formatter.extract_violations(report) == []
    advisory = print_formatter.extract_violations(report, advisory=True)
    assert [(v.component, v.severity) for v in advisory] == [
        ("OrConstraintComponent", "Warning")
    ]


def test_extract_violations_same_message_kept_apart_by_component():
    """One custom sh:message on two constraints still yields two violations."""
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:lanes ; sh:datatype xsd:integer ; sh:minInclusive 0 ;
                  sh:message "lanes must be a non-negative integer" ] .
"""
    _, report = _report(shapes, 'ex:road a ex:Road ; ex:lanes "five" .')

    violations = print_formatter.extract_violations(report)

    assert {v.message for v in violations} == {"lanes must be a non-negative integer"}
    assert [v.component for v in violations] == [
        "DatatypeConstraintComponent",
        "MinInclusiveConstraintComponent",
    ]


def test_extract_violations_renders_complex_paths_without_blank_node_ids():
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ( ex:format ex:mimeType ) ; sh:minCount 1 ] ;
    sh:property [ sh:path [ sh:inversePath ex:owns ] ; sh:minCount 1 ] .
"""
    _, report = _report(shapes, "ex:road a ex:Road .")

    assert [v.path for v in print_formatter.extract_violations(report)] == [
        "^owns",
        "format/mimeType",
    ]


def test_render_path_shacl_notation():
    shapes = Graph().parse(
        data=PREFIXES
        + """
ex:a sh:path [ sh:alternativePath ( ex:p [ sh:oneOrMorePath ex:q ] ) ] .
ex:b sh:path [ sh:inversePath ( ex:p ex:q ) ] .
ex:c sh:path [ sh:zeroOrMorePath ex:p ] .
ex:d sh:path [ sh:zeroOrOnePath ex:p ] .
""",
        format="turtle",
    )
    SH = Namespace("http://www.w3.org/ns/shacl#")
    EX = Namespace("https://example.org/v1/")

    rendered = [
        print_formatter._render_path(shapes, shapes.value(EX[name], SH.path))
        for name in "abcd"
    ]

    assert rendered == ["(p|q+)", "^(p/q)", "p*", "p?"]


def test_extract_violations_shortens_long_node_renderings():
    """An sh:closed message renders the whole node; the violation keeps it short."""
    shapes = """
ex:RoadShape a sh:NodeShape ; sh:targetClass ex:Road ;
    sh:property [ sh:path ex:lane ; sh:node ex:LaneShape ] .
ex:LaneShape a sh:NodeShape ; sh:closed true ;
    sh:property [ sh:path ex:description ] .
"""
    data = 'ex:road a ex:Road ; ex:lane [ ex:description "{}" ; ex:extra "boom" ] .'
    _, report = _report(shapes, data.format("a long description " * 10))

    [violation] = print_formatter.extract_violations(report)

    assert violation.path == "lane/extra"
    assert violation.message == (
        'Node [ ... ] is closed. It cannot have value: Literal("boom")'
    )


def test_violation_message_fixes_hash_dependent_parts():
    """pySHACL lists sh:in values in set order and cuts node renderings off at a
    hash-dependent point; a violation's message must depend on neither."""
    one = "Value <urn:x> not in list ['ex:b', 'ex:c', 'ex:a']"
    other = "Value <urn:x> not in list ['ex:c', 'ex:a', 'ex:b']"
    assert print_formatter._violation_message(one) == (
        "Value <urn:x> not in list ['ex:a', 'ex:b', 'ex:c']"
    )
    assert print_formatter._violation_message(other) == (
        print_formatter._violation_message(one)
    )
    deep = "<http://recursion.too.deep>"
    cut = f"Node [ ex:p [ ex:q {deep} ] ] must conform to [ sh:path ex:p ]"
    assert print_formatter._violation_message(cut) == (
        "Node [ ... ] must conform to [ sh:path ex:p ]"
    )


def test_shorten_node_renderings_keeps_short_renderings():
    message = 'Less than 1 values on [ ex:id Literal("a") ]->ex:width'
    assert print_formatter._shorten_node_renderings(message) == message


def test_extract_violations_empty_graph_returns_no_violations():
    assert print_formatter.extract_violations(Graph()) == []
