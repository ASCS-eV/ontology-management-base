#!/usr/bin/env python3
"""
Unit tests for src.tools.utils.properties_updater.
"""

from pathlib import Path

from src.tools.utils import properties_updater


def test_extract_shacl_properties_from_ttl(temp_dir: Path):
    ttl = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .

ex:Shape a sh:NodeShape ;
  sh:property [
    sh:path ex:prop ;
    sh:minCount 1 ;
    sh:maxCount 2 ;
    sh:description "desc" ;
    sh:datatype ex:Type ;
  ] .
"""
    file_path = temp_dir / "shape.shacl.ttl"
    file_path.write_text(ttl)

    graph = properties_updater.parse_graph(file_path, "turtle")
    props = properties_updater.extract_shacl_properties(graph, "shape.shacl.ttl")

    assert len(props) == 1
    assert str(props[0].path).endswith("prop")
    assert str(props[0].shape).endswith("Shape")
    assert str(props[0].min_count) == "1"
    assert str(props[0].max_count) == "2"
    assert props[0].filename == "shape.shacl.ttl"


def test_prefix_helpers(temp_dir: Path):
    ttl = "@prefix ex: <http://example.org/> .\nex:Thing ex:prop ex:Other .\n"
    file_path = temp_dir / "data.ttl"
    file_path.write_text(ttl)

    graph = properties_updater.parse_graph(file_path, "turtle")
    prefixes = properties_updater.extract_prefixes(graph)
    assert "http://example.org/" in prefixes

    uri = "http://example.org/Thing"
    replaced = properties_updater._replace_with_prefix(
        uri, {"http://example.org/": "ex"}
    )
    assert replaced == ("ex", "Thing")
