#!/usr/bin/env python3
"""A negative fixture is one with a paired ``.expected`` snapshot — nothing else.

Three things are covered here:

1. **The rule itself** — ``omb.core.negative_fixtures`` decides from the snapshot beside a
   file, so the same file classifies identically wherever it sits. The previous behaviour
   read the parent directory's name, which meant a file's meaning changed when it moved.
2. **The repository's filing** — ``tests/data/{domain}/{valid,invalid}/`` is now a
   convention with no power over validation, so it can silently drift from the pairing.
   These tests are what stop that: a fixture filed under ``invalid/`` without a snapshot
   would quietly become ordinary data, and a snapshot appearing beside a ``valid/`` file
   would quietly excuse it from conformance.
3. **The recorded snapshot itself** — classification is path-independent, so what gets
   compared against a snapshot has to be too, or moving a fixture and its snapshot
   together (the one relocation the pairing rule was designed to tolerate) would still
   report a mismatch on the validated-file line.
"""

from pathlib import Path

from omb.core.negative_fixtures import (
    EXPECTED_SUFFIX,
    expected_snapshot_path,
    is_negative_fixture,
    snapshot_files_field,
)

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
TESTS_DATA_DIR = ROOT_DIR / "tests" / "data"
DATA_SUFFIXES = {".json", ".jsonld"}


def _data_files(test_type: str) -> list[Path]:
    return sorted(
        p
        for p in TESTS_DATA_DIR.glob(f"*/{test_type}/*")
        if p.suffix in DATA_SUFFIXES and p.is_file()
    )


# =============================================================================
# The rule
# =============================================================================


def test_snapshot_path_keeps_every_suffix_but_the_last(tmp_path: Path):
    """``case.v2.json`` pairs with ``case.v2.expected``, not ``case.expected``.

    The pairing is the semantic rule now, so it has to be predictable for any filename,
    not only the single-suffix ones the repository happens to use today.
    """
    assert expected_snapshot_path(tmp_path / "case.json").name == "case.expected"
    assert expected_snapshot_path(tmp_path / "case.jsonld").name == "case.expected"
    assert expected_snapshot_path(tmp_path / "case.v2.json").name == "case.v2.expected"


def test_classification_ignores_the_directory_name(tmp_path: Path):
    """A file means the same thing in ``invalid/``, in ``valid/`` and anywhere else."""
    for directory in ("invalid", "valid", "somewhere-else"):
        parent = tmp_path / directory
        parent.mkdir()
        bare = parent / "case.json"
        bare.write_text("{}")
        assert not is_negative_fixture(bare), (
            f"{directory}/case.json has no snapshot, so it is ordinary data "
            "regardless of the directory it sits in"
        )

        expected_snapshot_path(bare).write_text("recorded report")
        assert is_negative_fixture(bare), (
            f"{directory}/case.json has a snapshot, so it is a negative fixture "
            "regardless of the directory it sits in"
        )


def test_a_directory_is_not_a_snapshot(tmp_path: Path):
    """Only a regular file counts, so a stray ``case.expected/`` directory is ignored."""
    data = tmp_path / "case.json"
    data.write_text("{}")
    (tmp_path / f"case{EXPECTED_SUFFIX}").mkdir()
    assert not is_negative_fixture(data)


# =============================================================================
# The repository's filing must agree with the rule
# =============================================================================


def test_every_invalid_fixture_has_a_snapshot():
    """A fixture filed under ``invalid/`` without a snapshot is silently ordinary data.

    It would be conformance-checked and simply fail, instead of being compared against a
    recorded report - so the missing snapshot has to be an error here.
    """
    unpaired = [
        p.relative_to(ROOT_DIR).as_posix()
        for p in _data_files("invalid")
        if not is_negative_fixture(p)
    ]
    assert not unpaired, (
        "these fixtures are filed as invalid but have no .expected snapshot, so nothing "
        "pins how they fail; record one with `just validate --run check-failing-tests "
        "--data-paths <file> --update-expected`:\n  " + "\n  ".join(unpaired)
    )


def test_no_valid_fixture_has_a_snapshot():
    """A snapshot beside a ``valid/`` file would excuse it from conformance entirely."""
    paired = [
        p.relative_to(ROOT_DIR).as_posix()
        for p in _data_files("valid")
        if is_negative_fixture(p)
    ]
    assert not paired, (
        "these fixtures are filed as valid but have an .expected snapshot beside them, "
        "which makes them negative fixtures and removes them from conformance "
        "validation:\n  " + "\n  ".join(paired)
    )


def test_the_repository_actually_has_fixtures_of_both_kinds():
    """Guard against the two checks above passing because they found nothing."""
    assert _data_files("valid"), "no valid fixtures found; the checks would be vacuous"
    assert _data_files("invalid"), (
        "no invalid fixtures found; the checks would be vacuous"
    )


# =============================================================================
# The recorded snapshot must be as path-independent as the classification
# =============================================================================


def test_snapshot_files_field_drops_the_directory():
    """Only the filename survives, regardless of how deep the original path was."""
    assert snapshot_files_field(
        ["tests/data/manifest/invalid/fail_01_missing_license.json"]
    ) == ["fail_01_missing_license.json"]
    assert snapshot_files_field(["/tmp/elsewhere/nested/case.json"]) == ["case.json"]


def test_snapshot_files_field_is_stable_across_relocation():
    """The whole point: the same file reduces to the same entry wherever it lives.

    This is what makes moving a fixture and its snapshot together - the one
    relocation the pairing rule in this module was designed to tolerate - not
    report a spurious mismatch on the validated-file line.
    """
    original = snapshot_files_field(
        ["tests/data/manifest/invalid/fail_01_missing_license.json"]
    )
    moved = snapshot_files_field(["/tmp/anywhere/deeper/fail_01_missing_license.json"])
    assert original == moved


def test_snapshot_files_field_preserves_order_and_count():
    """Reducing to filenames is a plain map, not a filter or a re-sort."""
    files = ["a/one.json", "b/two.json", "c/three.json"]
    assert snapshot_files_field(files) == ["one.json", "two.json", "three.json"]
