"""
Ontology management tools.

This package contains utilities for managing ontologies, including:
- Registry generation and updates
- Documentation generation
- Validation tools

PUBLIC API:
===========
``omb.api`` is the supported surface for other repositories:

    from omb.api import check_negative_fixtures, validate_data

    validate_data(paths, artifacts=[...])          # data that must conform
    check_negative_fixtures(paths, artifacts=[...])  # data that must fail

Together with the result types it returns (``omb.core.result.ValidationResult``,
``ReturnCodes``, and ``omb.api.FixtureReport``), that is what carries a stability
promise. Everything else — resolvers, loaders, the validator classes, the CLI
modules — is internal and may change in any release.

Importing this package configures nothing: logging, output encoding and exit codes
are the calling application's business. OMB's own loggers live under the ``omb``
name, so ``logging.getLogger("omb")`` addresses all of them at once.

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
