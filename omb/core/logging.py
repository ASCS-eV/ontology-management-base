#!/usr/bin/env python3
"""
Logging - Centralized Logger Configuration

Provides a consistent logging interface for all modules in the validation suite.
Uses Python's standard logging module with a standardized format.

FEATURE SET:
============
1. get_logger - Get a configured logger for a module
2. configure_logging - Set up logging level and format globally
3. LogLevel - Enum for log level constants

USAGE:
======
    from omb.core.logging import get_logger

    logger = get_logger(__name__)

    def my_function():
        logger.info("Starting process")
        logger.debug("Detail: %s", some_var)
        logger.warning("Potential issue: %s", warning)
        logger.error("Failed: %s", error)

STANDALONE TESTING:
==================
    python3 -m omb.core.logging [--test] [--level DEBUG]

    Options:
      --test      Run self-tests
      --level     Set log level (DEBUG, INFO, WARNING, ERROR)

DEPENDENCIES:
=============
- logging (stdlib)

NOTES:
======
- All modules should use get_logger(__name__) for consistent naming
- CLI output (print) is for user-facing results; logging is for progress/debug
- Default level is INFO; use DEBUG for detailed tracing

LIBRARY VS APPLICATION:
=======================
``get_logger`` is library-safe: it *only* looks a logger up. It never installs a
handler on the root logger and never changes anybody's level, so importing OMB
cannot disturb the logging setup of the application that imports it.

``configure_logging`` is the application-side half and belongs in a ``main()``.
OMB's own CLI entry points call it; a library caller is free never to call it, in
which case OMB's records travel up to whatever the host application configured.

The single ``NullHandler`` on the ``omb`` parent logger is the standard way to keep
``logging.lastResort`` from printing OMB's warnings to stderr in a host that has not
configured logging at all (see the "Configuring Logging for a Library" section of
the Python logging HOWTO).
"""

import argparse
import logging
import sys
from enum import IntEnum
from typing import Optional

# Default format: timestamp - module - level - message
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SHORT_FORMAT = "%(levelname)s: %(message)s"

# Root of OMB's logger hierarchy. Every logger handed out by get_logger() sits under
# this name, so a host application can silence or re-route all of OMB with a single
# logging.getLogger("omb") call.
PACKAGE_LOGGER_NAME = "omb"

# Track if logging has been configured globally
_logging_configured = False


class LogLevel(IntEnum):
    """Log level constants matching Python's logging module."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def configure_logging(
    level: int = logging.INFO,
    format_string: str = None,
    stream: Optional[object] = None,
) -> None:
    """
    Configure logging globally for the application.

    **Application-level call.** It replaces the root logger's handlers, so it belongs
    in a ``main()`` — OMB's own CLI entry points call it — and must never be triggered
    by importing a module. A library consumer of :mod:`omb.api` should leave it alone
    and configure logging however it likes; OMB's records will follow.

    This should be called once at application startup (e.g., in main()).
    Subsequent calls will update the configuration.

    Args:
        level: Logging level (use LogLevel enum or logging constants)
        format_string: Custom format string (default: SHORT_FORMAT)
        stream: Output stream (default: sys.stderr)
    """
    global _logging_configured

    if format_string is None:
        format_string = SHORT_FORMAT

    if stream is None:
        stream = sys.stderr

    # Detach any handlers already on the root logger so a repeated call (a different
    # stream or level) takes effect instead of piling duplicates up. Deliberately not
    # basicConfig(force=True), which would also *close* those handlers: this function
    # can be called by an application that still owns them.
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    logging.basicConfig(
        level=level,
        format=format_string,
        stream=stream,
    )

    _logging_configured = True


def configure_cli_logging(level: int = logging.INFO) -> None:
    """Configure logging for a command-line entry point, once.

    The application-side counterpart to :func:`get_logger`: every OMB ``main()`` calls
    this so the package's progress messages reach the console, which used to happen as
    a side effect of the first ``get_logger`` call. Doing it here — and only here —
    keeps that output for CLI users without importing OMB reconfiguring logging for a
    library caller.

    No-op if :func:`configure_logging` has already run.
    """
    if not _logging_configured:
        configure_logging(level=level)


def get_logger(name: str) -> logging.Logger:
    """
    Get the logger for a module, without configuring anything.

    The returned logger keeps its full dotted name (``omb.utils.registry_resolver``),
    so a host application can address the whole package at once — silence it with
    ``logging.getLogger("omb").setLevel(logging.ERROR)``, or route it somewhere of its
    own choosing — and so OMB's records can never collide with a logger of the host's
    that happens to share a last path segment.

    This function deliberately performs no configuration. It used to call
    ``configure_logging()`` on first use, which removed every handler from the root
    logger; because modules call ``get_logger(__name__)`` at import time, merely
    importing OMB then silently dismantled the importing application's logging setup.

    Args:
        name: Module name (typically ``__name__``)

    Returns:
        Logger instance for *name*

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    _ensure_package_null_handler()
    return logging.getLogger(name)


def _ensure_package_null_handler() -> None:
    """Attach a single NullHandler to the ``omb`` logger.

    Without a handler anywhere in the chain, ``logging.lastResort`` prints WARNING and
    above straight to ``sys.stderr``. That is the right default for an application and
    the wrong one for a library: it makes OMB write to a stream the caller never asked
    it to write to. The NullHandler makes OMB silent by default; ``configure_logging``
    (or the host's own setup) is what turns output back on.
    """
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    if not any(isinstance(h, logging.NullHandler) for h in package_logger.handlers):
        package_logger.addHandler(logging.NullHandler())


def set_level(level: int) -> None:
    """
    Set the logging level for the root logger.

    Args:
        level: Logging level (use LogLevel enum or logging constants)
    """
    logging.getLogger().setLevel(level)


def enable_debug() -> None:
    """Enable DEBUG level logging."""
    set_level(LogLevel.DEBUG)


def enable_verbose() -> None:
    """Enable verbose (DEBUG) logging with detailed format."""
    configure_logging(level=LogLevel.DEBUG, format_string=DEFAULT_FORMAT)


def _run_tests() -> bool:
    """Run self-tests for the module."""
    import io

    print("Running logging self-tests...")
    all_passed = True

    # Test 1: get_logger returns a logger
    try:
        logger = get_logger("test_module")
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        print("PASS: get_logger returns Logger instance")
    except AssertionError as e:
        print(f"FAIL: get_logger - {e}")
        all_passed = False

    # Test 2: Logger keeps its full dotted name (addressable as a hierarchy)
    try:
        logger = get_logger("omb.utils.file_collector")
        assert logger.name == "omb.utils.file_collector"
        assert logger.parent is not None
        print("PASS: Logger keeps its full dotted name")
    except AssertionError as e:
        print(f"FAIL: Logger naming - {e}")
        all_passed = False

    # Test 3: configure_logging changes level
    try:
        test_stream = io.StringIO()
        configure_logging(level=LogLevel.DEBUG, stream=test_stream)
        logger = get_logger("test_level")
        logger.debug("Debug message")
        output = test_stream.getvalue()
        assert "Debug message" in output
        print("PASS: configure_logging sets level correctly")
    except AssertionError as e:
        print(f"FAIL: configure_logging - {e}")
        all_passed = False

    # Test 4: LogLevel enum values match logging constants
    try:
        assert LogLevel.DEBUG == logging.DEBUG
        assert LogLevel.INFO == logging.INFO
        assert LogLevel.WARNING == logging.WARNING
        assert LogLevel.ERROR == logging.ERROR
        print("PASS: LogLevel enum values correct")
    except AssertionError as e:
        print(f"FAIL: LogLevel enum - {e}")
        all_passed = False

    # Reset logging config
    configure_logging()

    print()
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests FAILED!")

    return all_passed


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set log level for demo",
    )

    args = parser.parse_args()

    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    # Demo logging
    level = getattr(LogLevel, args.level)
    configure_logging(level=level)

    logger = get_logger(__name__)
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")


if __name__ == "__main__":
    main()
