#!/usr/bin/env python3
"""Location of OMB's built-in data (imports/, artifacts/, ...).

Single source of truth for "where OMB's own data lives". Today OMB runs from a
source checkout, so this is the repository root. When OMB is shipped as an
installed wheel, this function becomes the sole place that changes (to resolve
the packaged data directory) — every built-in-data lookup routes through here.
"""

from pathlib import Path


def builtin_data_root() -> Path:
    """Return the directory that contains OMB's built-in ``imports/`` and
    ``artifacts/`` data (and, in a source checkout, ``tests/`` and ``docs/``).

    Source layout: the repository root. This file is ``omb/core/paths.py``, so the
    root is two parents above it — i.e. ``parents[2]`` (``[0]=core``, ``[1]=omb``,
    ``[2]=repo root``). Callers may still pass an explicit ``root_dir`` to override.
    """
    return Path(__file__).resolve().parents[2]
