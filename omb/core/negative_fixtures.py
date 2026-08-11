#!/usr/bin/env python3
"""What makes a data file a *negative fixture* — one that is meant to fail validation.

A data file is a negative fixture **if and only if** a snapshot file sits beside it,
carrying the same stem and the ``.expected`` suffix::

    tests/data/hdmap/invalid/fail_01_missing_license.json   <- the data
    tests/data/hdmap/invalid/fail_01_missing_license.expected  <- its recorded report

The pairing is the whole rule. Nothing infers intent from a directory name, so a file
means the same thing wherever it lives: copying it elsewhere, or handing it to
``--data-paths`` from outside the repository, cannot change how it is validated.

``tests/data/{domain}/{valid,invalid}/`` remains the repository's own filing convention and
is still how fixtures are *found*, but it carries no meaning for validation — the snapshot
does. ``tests/unit/test_negative_fixture_pairing.py`` asserts the two never drift apart.

Why the pairing rather than the directory: a negative fixture is only useful if its failure
is pinned to a recorded report, and the snapshot *is* that record. Keying off its presence
means the thing that makes a failure acceptable is the same thing that says what the failure
must look like. A directory name promises neither.
"""

from pathlib import Path

#: Suffix of the file holding a negative fixture's recorded validation report.
EXPECTED_SUFFIX = ".expected"


def expected_snapshot_path(data_path: Path) -> Path:
    """Return the ``.expected`` snapshot path that pairs with ``data_path``.

    Uses the stem, so every suffix but the last is preserved:
    ``case.v2.json`` pairs with ``case.v2.expected``, not ``case.expected``.
    """
    data_path = Path(data_path)
    return data_path.with_name(data_path.stem + EXPECTED_SUFFIX)


def is_negative_fixture(data_path: Path) -> bool:
    """True when ``data_path`` has a paired ``.expected`` snapshot beside it."""
    return expected_snapshot_path(data_path).is_file()
