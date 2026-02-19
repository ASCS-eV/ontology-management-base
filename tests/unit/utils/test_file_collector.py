#!/usr/bin/env python3
"""
Unit tests for src.tools.utils.file_collector module.

Tests file collection utilities including:
- collect_files_by_extension
- collect_turtle_files
- collect_jsonld_files
- collect_files_by_pattern
- collect_ontology_files
- collect_test_files
- collect_ontology_bundles
"""

from pathlib import Path

import pytest  # noqa: F401

from src.tools.utils.file_collector import (
    collect_files_by_extension,
    collect_files_by_pattern,
    collect_jsonld_files,
    collect_ontology_bundles,
    collect_ontology_files,
    collect_test_files,
    collect_turtle_files,
    discover_data_hierarchy,
    extract_jsonld_iris,
)


class TestCollectFilesByExtension:
    """Tests for collect_files_by_extension function."""

    def test_empty_paths_returns_empty_list(self):
        """Empty input should return empty list."""
        result = collect_files_by_extension([], ".ttl")
        assert result == []

    def test_single_extension_string(self, temp_dir):
        """Test collecting files with a single extension as string."""
        (temp_dir / "file1.ttl").write_text("")
        (temp_dir / "file2.ttl").write_text("")
        (temp_dir / "file3.json").write_text("{}")

        result = collect_files_by_extension([temp_dir], ".ttl", return_pathlib=True)

        assert len(result) == 2
        assert all(f.suffix == ".ttl" for f in result)

    def test_multiple_extensions_set(self, temp_dir):
        """Test collecting files with multiple extensions as set."""
        (temp_dir / "file1.json").write_text("{}")
        (temp_dir / "file2.jsonld").write_text("{}")
        (temp_dir / "file3.ttl").write_text("")

        result = collect_files_by_extension(
            [temp_dir], {".json", ".jsonld"}, return_pathlib=True
        )

        assert len(result) == 2
        assert all(f.suffix in {".json", ".jsonld"} for f in result)

    def test_recursive_directory_walk(self, temp_dir):
        """Test that subdirectories are searched recursively."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (temp_dir / "root.json").write_text("{}")
        (subdir / "nested.json").write_text("{}")

        result = collect_files_by_extension([temp_dir], ".json", return_pathlib=True)

        assert len(result) == 2

    def test_single_file_input(self, temp_dir):
        """Test with a single file as input."""
        file_path = temp_dir / "single.ttl"
        file_path.write_text("")

        result = collect_files_by_extension([file_path], ".ttl", return_pathlib=True)

        assert len(result) == 1
        assert result[0] == file_path

    def test_wrong_extension_ignored(self, temp_dir, capsys):
        """Test that files with wrong extension are ignored with warning."""
        file_path = temp_dir / "wrong.json"
        file_path.write_text("{}")

        result = collect_files_by_extension([file_path], ".ttl", warn_on_invalid=True)

        assert len(result) == 0
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_sort_and_deduplicate(self, temp_dir):
        """Test sorting and deduplication of results."""
        (temp_dir / "b.json").write_text("{}")
        (temp_dir / "a.json").write_text("{}")

        result = collect_files_by_extension(
            [temp_dir, temp_dir],  # Duplicate path
            ".json",
            sort_and_deduplicate=True,
        )

        assert len(result) == 2
        # Should be sorted
        assert "a.json" in str(result[0])

    def test_return_strings_by_default(self, temp_dir):
        """Test that strings are returned by default."""
        (temp_dir / "test.ttl").write_text("")

        result = collect_files_by_extension([temp_dir], ".ttl")

        assert all(isinstance(f, str) for f in result)

    def test_return_pathlib_when_requested(self, temp_dir):
        """Test that Path objects are returned when requested."""
        (temp_dir / "test.ttl").write_text("")

        result = collect_files_by_extension([temp_dir], ".ttl", return_pathlib=True)

        assert all(isinstance(f, Path) for f in result)

    def test_nonexistent_path_warning(self, temp_dir, capsys):
        """Test warning for nonexistent paths."""
        result = collect_files_by_extension(
            [temp_dir / "nonexistent"], ".ttl", warn_on_invalid=True
        )

        assert result == []
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestCollectTurtleFiles:
    """Tests for collect_turtle_files convenience function."""

    def test_collects_ttl_files(self, temp_dir):
        """Test that .ttl files are collected."""
        (temp_dir / "ontology.ttl").write_text("")
        (temp_dir / "shapes.shacl.ttl").write_text("")
        (temp_dir / "data.json").write_text("{}")

        result = collect_turtle_files([temp_dir], return_pathlib=True)

        assert len(result) == 2
        assert all(f.suffix == ".ttl" for f in result)


class TestCollectJsonldFiles:
    """Tests for collect_jsonld_files convenience function."""

    def test_collects_json_and_jsonld_files(self, temp_dir):
        """Test that both .json and .jsonld files are collected."""
        (temp_dir / "data.json").write_text("{}")
        (temp_dir / "context.jsonld").write_text("{}")
        (temp_dir / "ontology.ttl").write_text("")

        result = collect_jsonld_files([temp_dir], return_pathlib=True)

        assert len(result) == 2
        assert all(f.suffix in {".json", ".jsonld"} for f in result)


class TestCollectFilesByPattern:
    """Tests for collect_files_by_pattern function."""

    def test_glob_pattern(self, temp_dir):
        """Test glob pattern matching."""
        (temp_dir / "domain.shacl.ttl").write_text("")
        (temp_dir / "domain.owl.ttl").write_text("")
        (temp_dir / "other.ttl").write_text("")

        result = collect_files_by_pattern([temp_dir], "*.shacl.ttl")

        assert len(result) == 1
        assert "shacl" in str(result[0])

    def test_recursive_pattern(self, temp_dir):
        """Test recursive glob pattern."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (temp_dir / "root.json").write_text("{}")
        (subdir / "nested.json").write_text("{}")

        result = collect_files_by_pattern([temp_dir], "**/*.json")

        assert len(result) == 2


class TestCollectOntologyFiles:
    """Tests for collect_ontology_files function."""

    def test_finds_standard_files(self, temp_dir):
        """Test finding files with standard naming convention."""
        domain_dir = temp_dir / "manifest"
        domain_dir.mkdir()
        (domain_dir / "manifest.owl.ttl").write_text("")
        (domain_dir / "manifest.shacl.ttl").write_text("")
        (domain_dir / "manifest.context.jsonld").write_text("{}")

        result = collect_ontology_files(domain_dir)

        assert result["ontology"] is not None
        assert result["shacl"] is not None
        assert len(result["shacl"]) == 1
        assert result["context"] is not None

    def test_multiple_shacl_files(self, temp_dir):
        """Test collecting multiple SHACL files."""
        domain_dir = temp_dir / "domain"
        domain_dir.mkdir()
        (domain_dir / "domain.owl.ttl").write_text("")
        (domain_dir / "domain.shacl.ttl").write_text("")
        (domain_dir / "domain.extra.shacl.ttl").write_text("")

        result = collect_ontology_files(domain_dir)

        assert result["shacl"] is not None
        assert len(result["shacl"]) == 2

    def test_missing_files(self, temp_dir):
        """Test when some files are missing."""
        domain_dir = temp_dir / "incomplete"
        domain_dir.mkdir()
        (domain_dir / "incomplete.owl.ttl").write_text("")

        result = collect_ontology_files(domain_dir)

        assert result["ontology"] is not None
        assert result["shacl"] is None
        assert result["context"] is None


class TestCollectTestFiles:
    """Tests for collect_test_files function."""

    def test_collect_valid_files(self, temp_dir):
        """Test collecting files from valid/ subdirectory."""
        valid_dir = temp_dir / "valid"
        valid_dir.mkdir()
        (valid_dir / "test1.json").write_text("{}")
        (valid_dir / "test2.json").write_text("{}")

        result = collect_test_files(temp_dir, valid=True)

        assert len(result) == 2

    def test_collect_invalid_files(self, temp_dir):
        """Test collecting files from invalid/ subdirectory."""
        invalid_dir = temp_dir / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "fail1.json").write_text("{}")

        result = collect_test_files(temp_dir, valid=False)

        assert len(result) == 1

    def test_nonexistent_subdir(self, temp_dir):
        """Test when valid/invalid directory doesn't exist."""
        result = collect_test_files(temp_dir, valid=True)

        assert result == []


class TestCollectOntologyBundles:
    """Tests for collect_ontology_bundles function."""

    def test_discovers_bundles(self, temp_dir):
        """Test discovering ontology bundles."""
        domain_dir = temp_dir / "manifest"
        domain_dir.mkdir()
        (domain_dir / "manifest.owl.ttl").write_text("")
        (domain_dir / "manifest.shacl.ttl").write_text("")
        (domain_dir / "manifest.context.jsonld").write_text("{}")

        result = collect_ontology_bundles(temp_dir)

        assert "manifest" in result
        assert result["manifest"]["ontology"] is not None

    def test_skips_dirs_without_owl(self, temp_dir):
        """Test that directories without OWL file are skipped."""
        domain_dir = temp_dir / "incomplete"
        domain_dir.mkdir()
        (domain_dir / "incomplete.shacl.ttl").write_text("")

        result = collect_ontology_bundles(temp_dir)

        assert "incomplete" not in result

    def test_with_tests_dir(self, temp_dir):
        """Test bundle discovery with tests directory."""
        artifacts_dir = temp_dir / "artifacts"
        artifacts_dir.mkdir()
        domain_dir = artifacts_dir / "manifest"
        domain_dir.mkdir()
        (domain_dir / "manifest.owl.ttl").write_text("")

        tests_dir = temp_dir / "tests"
        tests_dir.mkdir()
        valid_dir = tests_dir / "manifest" / "valid"
        valid_dir.mkdir(parents=True)
        (valid_dir / "manifest_instance.json").write_text("{}")

        result = collect_ontology_bundles(artifacts_dir, tests_dir)

        assert "manifest" in result
        assert result["manifest"]["instance"] is not None

    def test_nonexistent_base_dir(self, temp_dir, capsys):
        """Test with nonexistent base directory."""
        result = collect_ontology_bundles(temp_dir / "nonexistent")

        assert result == {}
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestExtractJsonldIris:
    """Tests for extract_jsonld_iris function."""

    def test_extracts_at_id(self, temp_dir):
        """Test extracting @id from JSON-LD."""
        file = temp_dir / "test.json"
        file.write_text('{"@id": "did:web:example.com:test", "@type": "TestClass"}')
        root_id, refs = extract_jsonld_iris(file)
        assert root_id == "did:web:example.com:test"
        assert len(refs) == 0

    def test_extracts_id_without_at(self, temp_dir):
        """Test extracting id field without @ prefix."""
        file = temp_dir / "test.json"
        file.write_text('{"id": "urn:example:123", "@type": "TestClass"}')
        root_id, refs = extract_jsonld_iris(file)
        assert root_id == "urn:example:123"

    def test_returns_none_for_no_id(self, temp_dir):
        """Test returns None when no @id or id field."""
        file = temp_dir / "test.json"
        file.write_text('{"@type": "TestClass", "name": "Test"}')
        root_id, refs = extract_jsonld_iris(file)
        assert root_id is None

    def test_returns_none_for_invalid_json(self, temp_dir):
        """Test returns None for invalid JSON."""
        file = temp_dir / "test.json"
        file.write_text('{"invalid json')
        root_id, refs = extract_jsonld_iris(file)
        assert root_id is None
        assert len(refs) == 0

    def test_extracts_nested_ids(self, temp_dir):
        """Test extracting nested @id references."""
        file = temp_dir / "test.json"
        file.write_text(
            """{
            "@id": "did:web:example.com:main",
            "@type": "TestClass",
            "hasReference": {"@id": "did:web:example.com:ref1"},
            "hasOther": {"@id": "did:web:example.com:ref2"}
        }"""
        )
        root_id, refs = extract_jsonld_iris(file)
        assert root_id == "did:web:example.com:main"
        assert "did:web:example.com:ref1" in refs
        assert "did:web:example.com:ref2" in refs
        assert "did:web:example.com:main" not in refs  # Root excluded

    def test_excludes_blank_nodes(self, temp_dir):
        """Test that blank nodes are excluded."""
        file = temp_dir / "test.json"
        file.write_text(
            """{
            "@id": "did:web:example.com:main",
            "nested": {"@id": "_:blank1", "value": "test"}
        }"""
        )
        _, refs = extract_jsonld_iris(file)
        assert "_:blank1" not in refs

    def test_extracts_from_arrays(self, temp_dir):
        """Test extracting from arrays."""
        file = temp_dir / "test.json"
        file.write_text(
            """{
            "@id": "did:web:example.com:main",
            "items": [
                {"@id": "did:web:example.com:item1"},
                {"@id": "did:web:example.com:item2"}
            ]
        }"""
        )
        _, refs = extract_jsonld_iris(file)
        assert "did:web:example.com:item1" in refs
        assert "did:web:example.com:item2" in refs


class TestDiscoverDataHierarchy:
    """Tests for discover_data_hierarchy function."""

    def test_single_file_without_refs(self, temp_dir):
        """Single file with no references is top-level."""
        file = temp_dir / "standalone.json"
        file.write_text('{"@id": "did:web:test:standalone", "@type": "Thing"}')

        top_level, iri_map = discover_data_hierarchy([file])

        assert len(top_level) == 1
        assert top_level[0] == file
        assert "did:web:test:standalone" in iri_map

    def test_file_with_fixture_reference(self, temp_dir):
        """File referencing another file - ref becomes fixture."""
        main_file = temp_dir / "main.json"
        main_file.write_text(
            """{
            "@id": "did:web:test:main",
            "@type": "TestClass",
            "hasRef": {"@id": "did:web:test:fixture"}
        }"""
        )
        fixture_file = temp_dir / "fixture.json"
        fixture_file.write_text('{"@id": "did:web:test:fixture", "@type": "Fixture"}')

        top_level, iri_map = discover_data_hierarchy([temp_dir])

        # Only main should be top-level since fixture is referenced
        assert len(top_level) == 1
        assert top_level[0].name == "main.json"
        assert "did:web:test:fixture" in iri_map
        assert iri_map["did:web:test:fixture"].name == "fixture.json"

    def test_directory_recursive_scan(self, temp_dir):
        """Test recursive directory scanning."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        main_file = temp_dir / "main.json"
        main_file.write_text('{"@id": "did:web:test:main", "@type": "TestClass"}')
        nested_file = subdir / "nested.json"
        nested_file.write_text('{"@id": "did:web:test:nested", "@type": "TestClass"}')

        top_level, iri_map = discover_data_hierarchy([temp_dir])

        assert len(top_level) == 2
        assert len(iri_map) == 2

    def test_explicit_file_always_validated(self, temp_dir):
        """Explicitly specified file is always top-level even if referenced."""
        main_file = temp_dir / "main.json"
        main_file.write_text(
            """{
            "@id": "did:web:test:main",
            "hasRef": {"@id": "did:web:test:fixture"}
        }"""
        )
        fixture_file = temp_dir / "fixture.json"
        fixture_file.write_text('{"@id": "did:web:test:fixture", "@type": "Fixture"}')

        # Explicitly request both files
        top_level, iri_map = discover_data_hierarchy([main_file, fixture_file])

        # Both should be validated since both were explicitly specified
        assert len(top_level) == 2
        assert any(f.name == "main.json" for f in top_level)
        assert any(f.name == "fixture.json" for f in top_level)

    def test_multiple_dirs(self, temp_dir):
        """Test with multiple directories."""
        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "file1.json").write_text('{"@id": "did:web:test:file1"}')
        (dir2 / "file2.json").write_text('{"@id": "did:web:test:file2"}')

        top_level, iri_map = discover_data_hierarchy([dir1, dir2])

        assert len(top_level) == 2
        assert len(iri_map) == 2

    def test_empty_paths(self, temp_dir):
        """Test with empty input."""
        top_level, iri_map = discover_data_hierarchy([])
        assert top_level == []
        assert iri_map == {}

    def test_nonexistent_path_ignored(self, temp_dir):
        """Non-existent paths should not cause crash."""
        valid_file = temp_dir / "valid.json"
        valid_file.write_text('{"@id": "did:web:test:valid"}')

        top_level, iri_map = discover_data_hierarchy(
            [valid_file, temp_dir / "nonexistent.json"]
        )

        # Should still process valid file
        assert len(top_level) == 1
        assert top_level[0].name == "valid.json"
