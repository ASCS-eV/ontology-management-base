# Ontology Management Base - AI Assistant Instructions

This repository contains a validation suite for ontology artifacts (OWL, SHACL, JSON-LD).

## Build, Test, and Lint Commands

```bash
# Install dev dependencies + pre-commit hooks
make install-dev

# Lint and format
make lint
make format

# Run full validation suite (catalog-driven)
python3 -m src.tools.validators.validation_suite

# Validate specific domain
python3 -m src.tools.validators.validation_suite --domain manifest

# Validate arbitrary data paths (auto-discovers fixtures)
python3 -m src.tools.validators.validation_suite --data-paths ./my_data.json

# Validate with external artifact directories
python3 -m src.tools.validators.validation_suite --run check-data-conformance \
    --data-paths ./examples/credential.json \
    --artifacts ./artifacts ../external-repo/artifacts

# Use specific inference mode (rdfs, owlrl, none, both)
python3 -m src.tools.validators.validation_suite --domain hdmap --inference-mode owlrl

# Run specific validation checks
python3 -m src.tools.validators.validation_suite --run check-data-conformance --domain hdmap

# Run tests
pytest tests/

# Run a single test file
pytest tests/unit/utils/test_file_collector.py

# Run tests matching a pattern
pytest tests/ -k "test_load"

# Run with coverage
pytest tests/ --cov=src/tools --cov-report=html

# Run full validation suite via Make
make test

# Run a single domain via Make
make test-domain DOMAIN=hdmap

# Run module self-tests
python3 -m src.tools.validators.syntax_validator --test
python3 -m src.tools.utils.file_collector --test
```

## Instruction Files

Read these BEFORE making changes:

| Topic                           | File                                                                       |
| ------------------------------- | -------------------------------------------------------------------------- |
| Agent instructions              | [../AGENTS.md](../AGENTS.md)                                                |
| Module structure & dependencies | [instructions/architecture.md](instructions/architecture.md)               |
| Code style & patterns           | [instructions/coding-standards.md](instructions/coding-standards.md)       |
| Validation pipeline             | [instructions/validation-workflow.md](instructions/validation-workflow.md) |
| Testing requirements            | [instructions/testing.md](instructions/testing.md)                         |
| Domain terminology              | [instructions/glossary.md](instructions/glossary.md)                       |

## Core Principles

1. **Catalog-Driven Architecture**: All file discovery goes through XML catalogs. No fallbacks to file system scanning.

2. **Single Responsibility**:
   - `registry_updater.py` → WRITES catalogs
   - `registry_resolver.py` → READS catalogs
   - `file_collector.py` → INTERNAL use by registry_updater only
   - Validators → NEVER discover files directly

3. **Fail Fast**: If a resource is not in a catalog, raise an error. No silent fallbacks.

4. **Centralized Utilities**:
   - Logging → `core/logging.py`
   - IRI string operations → `core/iri_utils.py`
   - Graph operations → `utils/graph_loader.py`
   - Path resolution → `utils/registry_resolver.py`
   - Path normalization → `utils/file_collector.py` (`PathsInput`, `normalize_paths_to_list`)

## High-Level Architecture

- **Layered modules**: `src/tools/core` (foundations) → `src/tools/utils` (catalog + graph helpers) → `src/tools/validators` (CLI pipeline). No upward imports.
- **Catalog-driven discovery**: XML catalogs in `artifacts/`, `imports/`, and `tests/` are the single source of truth for file resolution.
- **Validation pipeline**: `check-syntax` → `check-artifact-coherence` → `check-data-conformance` → `check-failing-tests` (domain mode only for coherence/failing tests).
- **Data paths mode** builds a temporary in-memory catalog from `--data-paths` inputs, then runs the standard pipeline.

## Key Conventions

- **Catalog responsibilities**: `registry_updater.py` writes catalogs (and is the only user of `file_collector.py`); `registry_resolver.py` reads catalogs. Validators never scan the filesystem.
- **Ontology IRI policy**: new domains use `w3id.org/ascs-ev/envited-x/{domain}/v{n}`. When bumping a legacy `gaia-x4plcaad` ontology, switch to the ASCS-eV namespace and add `owl:priorVersion`.
- **Module docstrings** must follow the template in `coding-standards.md`, and modules include a `main()` + `_run_tests()` for self-testing.
- **Logging/output**: use `get_logger(__name__)` for progress; `print()` only for final CLI output; normalize paths with `normalize_path_for_display()`.
- **Errors/return codes**: raise specific exceptions (no silent `None`), and use `ReturnCodes` from `core/result.py`.
- **Test data**: invalid instances live in `tests/data/{domain}/invalid/` and require a matching `.expected` file.
- **Artifact changes**: run `python3 -m src.tools.utils.registry_updater` (pre-commit hooks also update catalogs/README/PROPERTIES).
- **Path input flexibility**: Collection functions accept `PathsInput` (single path or list) - use `normalize_paths_to_list()` from `file_collector.py` when needed.

## Before You Code

1. Check which catalog(s) are involved
2. Verify the module responsibilities match the architecture
3. Use centralized utilities (don't reinvent logging, IRI parsing, etc.)
4. Add tests for new functionality

## Common Mistakes to Avoid

- ❌ **Don't bypass catalogs** - Never scan the file system directly in validators
- ❌ **Don't use `file_collector.py` outside `registry_updater.py`**
- ❌ **Don't use `os.path`** - Use `pathlib.Path` instead
- ❌ **Don't silently return `None`** - Raise specific exceptions
- ❌ **Don't use `print()` for logging** - Use `logger` from `core/logging.py`
- ❌ **Don't duplicate path normalization** - Use `normalize_paths_to_list()` or `normalize_path_for_display()`

## Key Imports

```python
# Logging
from src.tools.core.logging import get_logger
logger = get_logger(__name__)

# Path resolution (READ from catalogs)
from src.tools.utils.registry_resolver import RegistryResolver

# Graph loading
from src.tools.utils.graph_loader import load_graph, load_jsonld_files

# Return codes
from src.tools.core.result import ReturnCodes, ValidationResult

# Path utilities
from src.tools.utils.file_collector import PathsInput, normalize_paths_to_list
from src.tools.utils.print_formatter import normalize_path_for_display

# Syntax validation (unified API)
from src.tools.validators.syntax_validator import (
    check_json_wellformedness,
    check_turtle_wellformedness,
)
```
