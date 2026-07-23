"""
Ontology management tools.

This package contains utilities for managing ontologies, including:
- Registry generation and updates
- Documentation generation
- Validation tools

The package version has a single source of truth: the ``version`` field in
``pyproject.toml``. ``__version__`` below is *derived* from the installed package
metadata (which the build backend fills in from ``pyproject.toml``), so it can
never drift from the published distribution. When running from a source tree that
has not been installed, the metadata is unavailable and a clearly-marked
placeholder is used instead.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("ontology-management-base")
except PackageNotFoundError:  # not installed (e.g. a bare, uninstalled source tree)
    __version__ = "0.0.0+unknown"
