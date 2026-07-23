#!/usr/bin/env python3
"""
Core abstractions for the ontology management tools.

This package provides shared types, constants, and result objects used
throughout the validation and processing modules.

Contents:
    - constants: Shared constants (FAST_STORE, etc.)
    - result: ValidationResult dataclass and ReturnCodes enum
    - logging: Centralized logger configuration
    - iri_utils: IRI string manipulation utilities

Usage:
    from omb.core import ValidationResult, ReturnCodes
    from omb.core.constants import FAST_STORE
    from omb.core.logging import get_logger
    from omb.core.iri_utils import get_local_name
"""

from .constants import FAST_STORE
from .iri_utils import get_local_name, get_namespace, is_did_web, parse_did_web
from .logging import LogLevel, configure_logging, get_logger
from .result import ReturnCodes, ValidationResult

__all__ = [
    # Constants
    "FAST_STORE",
    # Result types
    "ReturnCodes",
    "ValidationResult",
    # Logging
    "get_logger",
    "configure_logging",
    "LogLevel",
    # IRI utilities
    "get_local_name",
    "get_namespace",
    "is_did_web",
    "parse_did_web",
]
