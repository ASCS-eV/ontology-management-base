#!/usr/bin/env python3
"""Lock the validation-core vs optional-[publish] dependency split (A4)."""

import pathlib
import subprocess
import sys
import tomllib

_PYPROJECT = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
_REPO_ROOT = _PYPROJECT.parent


def _manifest() -> dict:
    return tomllib.loads(_PYPROJECT.read_text("utf-8"))


def test_core_deps_are_validation_only():
    """Core runtime deps must be exactly rdflib + pyshacl + oxrdflib."""
    core = _manifest()["project"]["dependencies"]
    joined = " ".join(core)
    assert "rdflib" in joined
    assert "pyshacl" in joined
    assert "oxrdflib" in joined  # HARD core: default store is too slow
    assert "keycloak" not in joined
    assert "requests" not in joined


def test_publish_extra_holds_the_publication_stack():
    """keycloak_client + requests live in the optional [publish] extra."""
    extras = _manifest()["project"]["optional-dependencies"]
    assert "publish" in extras
    joined = " ".join(extras["publish"])
    assert "keycloak_client" in joined
    assert "requests" in joined


def test_validate_import_path_excludes_publish_stack():
    """Importing the public API must not drag in requests/keycloak.

    Run in a fresh interpreter so sys.modules is clean; this holds even if the
    publish extra happens to be installed in the dev environment.
    """
    probe = (
        "import sys; import omb.api;"  # the public validate entry point
        "leaked=[m for m in ('requests','keycloak') if m in sys.modules];"
        "print('LEAKED', leaked); sys.exit(1 if leaked else 0)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"publish stack leaked onto import path:\n{proc.stdout}\n{proc.stderr}"
    )
