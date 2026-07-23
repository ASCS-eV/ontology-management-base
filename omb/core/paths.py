#!/usr/bin/env python3
"""Location of OMB's built-in data (imports/, artifacts/, ...).

Single source of truth for "where OMB's own data lives". Today OMB runs from a
source checkout, so this is the repository root. When OMB is shipped as an
installed wheel, this function becomes the sole place that changes (to resolve
the packaged data directory) — every built-in-data lookup routes through here.
"""

from importlib import resources
from pathlib import Path


def builtin_data_root() -> Path:
    """Return the directory that contains OMB's built-in data — ``imports/``,
    ``artifacts/`` and ``docs/registry.json``.

    Installed wheel: the data is bundled *inside* the package at ``omb/data/`` (via
    the hatchling ``force-include`` mapping in ``pyproject.toml``); this function
    returns that directory so an installed ``omb`` validates without a source checkout.

    Source checkout / editable install: ``omb/data/`` does not exist (``force-include``
    only populates the built wheel), so we fall back to the repository root. This file
    is ``omb/core/paths.py`` → the root is ``parents[2]`` (``[0]=core``, ``[1]=omb``,
    ``[2]=repo root``). Callers may still pass an explicit ``root_dir`` to override
    where relevant.
    """
    packaged = Path(str(resources.files("omb"))) / "data"
    if (packaged / "imports").is_dir():
        return packaged
    return Path(__file__).resolve().parents[2]
