# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Central repository for **Gaia-X 25.11 compliant ontologies** for the ENVITED-X Ecosystem. Provides OWL ontology definitions, SHACL validation shapes, JSON-LD context files, and a Python validation suite.

**Key URLs:**
- Documentation: https://ascs-ev.github.io/ontology-management-base/
- Repository: https://github.com/ASCS-eV/ontology-management-base

## Essential Commands

```bash
# Install (dev mode with pre-commit hooks)
pip install -e ".[dev]" && pre-commit install

# Run full validation suite
python3 -m src.tools.validators.validation_suite

# Validate specific domain(s)
python3 -m src.tools.validators.validation_suite --domain manifest hdmap

# Run a specific validation check only
python3 -m src.tools.validators.validation_suite --run check-data-conformance --domain hdmap

# Validate arbitrary files (for pre-commit / ad-hoc)
python3 -m src.tools.validators.validation_suite --path ./my_data.json

# Run all pytest tests
pytest tests/

# Run a single test file
pytest tests/unit/utils/test_file_collector.py

# Run tests matching a pattern
pytest tests/ -k "test_load"

# Run tests with coverage
pytest tests/ --cov=src/tools --cov-report=html

# Lint and format
make lint       # pre-commit on all files
make format     # black + isort on src/

# Run module self-tests
python3 -m src.tools.utils.file_collector --test

# Local docs server
DOCS_SITE_URL=http://127.0.0.1:8000/ontology-management-base mkdocs serve

# Update catalogs after artifact changes
python3 -m src.tools.utils.registry_updater
```

**Installed CLI entry points** (after `pip install -e .`):
- `onto-validate` → `validation_suite:main`
- `onto-check-conformance` → `conformance_validator:main`
- `onto-check-coherence` → `coherence_validator:main`
- `onto-generate-docs` → `properties_updater:main`

## Architecture

### Module Hierarchy

```
src/tools/
├── core/           # Foundation (no internal deps) - constants, logging, result codes, IRI utils
├── utils/          # Catalog I/O + graph loading - depends on core/
└── validators/     # Validation CLI - depends on core/ + utils/
    └── shacl/      # SHACL validation internals (ShaclValidator, schema discovery, inference)
```

**Dependency rule:** Never import upward (utils cannot import from validators).

### Catalog-Driven Design

All file discovery goes through XML catalogs. Validators never scan the filesystem directly.

| Module | Responsibility |
|--------|----------------|
| `registry_updater.py` | WRITES catalogs, uses `file_collector.py` for discovery |
| `registry_resolver.py` | READS catalogs, resolves IRIs to paths |
| `file_collector.py` | Shared file discovery utilities (used by updater ONLY) |

### Catalog Locations

- `artifacts/catalog-v001.xml` — Ontology IRIs → local OWL/SHACL/context files
- `imports/catalog-v001.xml` — Base ontologies (RDF, RDFS, OWL, SKOS)
- `tests/catalog-v001.xml` — Test data files + fixtures (mock external `did:web:` refs)

### Validation Pipeline

Four checks run in sequence (selectable via `--run`):
1. **check-syntax** — JSON/Turtle well-formedness
2. **check-artifact-coherence** — SHACL targets exist in OWL (domain mode only)
3. **check-data-conformance** — SHACL validation of instance data (loads data → extracts types → discovers schemas → resolves `did:web:` fixtures → applies RDFS inference → runs pyshacl)
4. **check-failing-tests** — Invalid data in `tests/data/{domain}/invalid/` fails as expected, matched against `.expected` files (domain mode only)

### Pre-commit Hooks

Auto-triggered on relevant file changes (configured in `.pre-commit-config.yaml`):
- **black / isort / flake8** — Python formatting and linting
- **jsonld-lint / turtle-lint** — Syntax validation for `.json`/`.jsonld`/`.ttl` files
- **update-registry** — Regenerates `artifacts/catalog-v001.xml` when artifact files change
- **update-properties** — Regenerates `PROPERTIES.md` documentation
- **update-readme** — Updates the catalog table in `README.md`

## Key Imports

```python
from src.tools.core.logging import get_logger
from src.tools.core.result import ReturnCodes, ValidationResult
from src.tools.core.constants import FAST_STORE, Extensions, Namespaces
from src.tools.core.iri_utils import ...  # IRI string manipulation
from src.tools.utils.registry_resolver import RegistryResolver
from src.tools.utils.graph_loader import load_graph, load_jsonld_files
from src.tools.utils.print_formatter import normalize_path_for_display

logger = get_logger(__name__)
```

## File Types

| Extension | Purpose | Location |
|-----------|---------|----------|
| `.owl.ttl` | OWL ontology definitions | `artifacts/{domain}/` |
| `.shacl.ttl` | SHACL validation shapes | `artifacts/{domain}/` |
| `.context.jsonld` | JSON-LD context files | `artifacts/{domain}/` |
| `.json` / `.jsonld` | JSON-LD instance data | `tests/data/{domain}/valid/` or `invalid/` |
| `.expected` | Expected error output for invalid test data | `tests/data/{domain}/invalid/` |
| `catalog-v001.xml` | OASIS XML catalog | `artifacts/`, `imports/`, `tests/` |

## Coding Conventions

- **Python 3.12+** with type hints on public APIs
- **pathlib.Path** (never `os.path`)
- **Centralized logging** via `get_logger(__name__)`; reserve `print()` for final user output
- **Fail fast** — raise specific exceptions, no silent `None` returns
- **Test naming** — `test_{function}_{scenario}_{expected}`
- **Import order** — stdlib, third-party, local core, local utils
- **Path display** — use `normalize_path_for_display()` to avoid leaking absolute paths in output
- **Conventional commits** — short imperative subjects prefixed with `feat:`, `fix:`, `docs:`, or scoped like `feat(ontology): ...`

## Instruction Files

Read these before making changes:

| Topic | File |
|-------|------|
| Module structure | `.github/instructions/architecture.md` |
| Code style | `.github/instructions/coding-standards.md` |
| Validation pipeline | `.github/instructions/validation-workflow.md` |
| Testing requirements | `.github/instructions/testing.md` |
| Domain terminology | `.github/instructions/glossary.md` |

## Change Documentation

When making changes to the codebase, always update these two files in `.playground/` (gitignored):

| File | Purpose |
|------|---------|
| `.playground/change-summary.md` | Detailed markdown summary of all changes grouped by severity/category, including file paths, problem descriptions, and fixes applied |
| `.playground/commit-message.md` | Conventional commit message with bullet points, ready for copy-paste into `git commit` |

Update both files **before** presenting the final result to the user. If a session involves multiple rounds of changes, keep these files in sync with the cumulative state.

## Common Mistakes to Avoid

- Bypassing catalogs with direct filesystem scanning in validators
- Using `file_collector.py` outside of `registry_updater.py`
- Using `os.path` instead of `pathlib.Path`
- Silent `None` returns instead of raising exceptions
- Using `print()` for internal progress (use `logger`)
- Leaking absolute paths in output (use `normalize_path_for_display`)
