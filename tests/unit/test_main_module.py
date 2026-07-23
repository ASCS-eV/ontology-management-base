#!/usr/bin/env python3
"""Verify ``python -m omb`` runs the validation suite CLI (the W1e __main__ entry)."""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_python_dash_m_omb_runs_validation_cli():
    """`python -m omb --help` must exit 0 and expose the validation suite's parser."""
    proc = subprocess.run(
        [sys.executable, "-m", "omb", "--help"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"`python -m omb --help` failed:\n{proc.stdout}\n{proc.stderr}"
    )
    # Proves __main__ delegated to validation_suite's argparse (a --run choice appears).
    assert "check-artifact-coherence" in proc.stdout
