#!/usr/bin/env python3
"""
Smoke tests for package __init__ modules under omb.
"""

import importlib


def test_tools_package_version():
    tools = importlib.import_module("omb")
    assert isinstance(tools.__version__, str)


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
