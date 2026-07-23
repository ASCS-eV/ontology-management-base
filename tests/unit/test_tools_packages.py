#!/usr/bin/env python3
"""
Smoke tests for package __init__ modules under omb.
"""

import importlib
import importlib.metadata
import pathlib
import tomllib

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_tools_package_version():
    tools = importlib.import_module("omb")
    assert isinstance(tools.__version__, str)


def test_version_is_single_sourced_from_pyproject():
    """The version has one source of truth (pyproject.toml); __version__ derives from it.

    ``omb.__version__`` is read from the installed distribution metadata, which the
    build backend fills in from ``pyproject.toml`` — so all three must agree, and the
    old hardcoded ``2.0.0`` must be gone. If installed metadata and pyproject disagree,
    the editable install is stale: reinstall with ``pip install -e . --no-deps``.
    """
    omb = importlib.import_module("omb")
    installed = importlib.metadata.version("ontology-management-base")
    declared = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text("utf-8"))[
        "project"
    ]["version"]

    assert omb.__version__ == installed, (
        "omb.__version__ must derive from installed metadata"
    )
    assert installed == declared, (
        f"installed metadata ({installed}) != pyproject ({declared}); "
        "reinstall with `pip install -e . --no-deps` after bumping the version"
    )
    assert omb.__version__ != "2.0.0", (
        "the old hardcoded 2.0.0 version drift must be gone"
    )


def test_core_exports():
    core = importlib.import_module("omb.core")
    assert "FAST_STORE" in core.__all__
    assert "ReturnCodes" in core.__all__
    assert "ValidationResult" in core.__all__


def test_utils_exports():
    utils = importlib.import_module("omb.utils")
    for name in ("RegistryResolver", "collect_jsonld_files", "load_graph"):
        assert hasattr(utils, name)


def test_validators_package_import():
    importlib.import_module("omb.validators")


def test_authhelper_package_import():
    importlib.import_module("omb.authhelper")


def test_uploaders_package_import():
    importlib.import_module("omb.uploaders")


def test_shacl_package_import():
    importlib.import_module("omb.validators.shacl")
