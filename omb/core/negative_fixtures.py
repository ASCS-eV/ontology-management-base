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
from typing import List

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


def snapshot_files_field(files_validated: List[str]) -> List[str]:
    """Reduce a validated-file list to bare filenames, for recording/comparison.

    A negative fixture's ``.expected`` snapshot pairs with its data file by stem,
    *inside the same directory* as ``is_negative_fixture`` requires. The directory is
    therefore never part of the pairing, and embedding a full path in the snapshot's
    validated-file line makes an otherwise-stable comparison depend on where the pair
    happens to live: moving both files together — the one relocation the pairing rule
    was designed to tolerate — still reported a mismatch on that line, because the same
    file resolves to a different display path depending on its distance from
    ``root_dir`` or the working directory (see ``normalize_path_for_display``).

    Recording only the filename keeps the snapshot exactly as path-independent as the
    classification it is being asked to confirm. Used only when building the report
    that is written to, or compared against, a ``.expected`` snapshot — every other
    console message keeps the full path, since there the location genuinely is the
    information being reported.
    """
    return [Path(f).name for f in files_validated]
