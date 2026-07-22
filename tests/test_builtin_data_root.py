#!/usr/bin/env python3
"""The built-in data-root seam decouples OMB's data from the caller's cwd (A3)."""

from pathlib import Path

from omb.api import validate_data
from omb.core.paths import builtin_data_root
from omb.utils.registry_resolver import RegistryResolver
from omb.validators.validation_suite import ROOT_DIR


def test_builtin_data_root_points_at_omb_data():
    root = builtin_data_root()
    assert (root / "imports" / "catalog-v001.xml").exists()
    assert (root / "artifacts" / "catalog-v001.xml").exists()


def test_root_dir_constant_uses_seam():
    assert ROOT_DIR == builtin_data_root()


def test_resolver_default_root_is_builtin_not_cwd(monkeypatch, tmp_path):
    """With no root_dir, the resolver must default to the built-in data root,
    NOT the process cwd (this would FAIL before A3, when the default was cwd)."""
    monkeypatch.chdir(tmp_path)
    resolver = RegistryResolver()
    assert resolver.root_dir == builtin_data_root()
    assert resolver.root_dir != Path(tmp_path).resolve()


def test_validation_is_cwd_independent(monkeypatch, tmp_path):
    """Validating an absolute data path must succeed from an unrelated cwd,
    because built-in schemas resolve via the seam, not via cwd."""
    gx = (builtin_data_root() / "tests" / "data" / "gx" / "valid").resolve()
    monkeypatch.chdir(tmp_path)
    result = validate_data([str(gx)])
    assert result.conforms is True
    assert result.shapes_loaded > 0
