# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Central repository for **Gaia-X 25.11 compliant ontologies** for the ENVITED-X Ecosystem, maintained by ASCS e.V. Provides OWL ontology definitions, SHACL validation shapes, JSON-LD context files, and a Python validation suite.

Forked from [GAIA-X4PLC-AAD/ontology-management-base](https://github.com/GAIA-X4PLC-AAD/ontology-management-base) (archived after `v0.1.0`). This is the active development home.

**Key URLs:**
- Documentation: https://ascs-ev.github.io/ontology-management-base/
- Repository: https://github.com/ASCS-eV/ontology-management-base

## Essential Commands

```bash
# One-command setup (creates .venv, installs dev dependencies, and pre-commit hooks)
make setup

# Run full validation suite
python3 -m src.tools.validators.validation_suite

# Validate specific domain(s)
python3 -m src.tools.validators.validation_suite --domain manifest hdmap

# Run a specific validation check only
python3 -m src.tools.validators.validation_suite --run check-data-conformance --domain hdmap

# Validate arbitrary files (auto-discovers fixtures from referenced IRIs)
python3 -m src.tools.validators.validation_suite --data-paths ./my_data.json

# Validate with external artifact directories
python3 -m src.tools.validators.validation_suite --run check-data-conformance \
    --data-paths ./examples/credential.json \
    --artifacts ./artifacts ../external-repo/artifacts

# Use specific inference mode (rdfs, owlrl, none, both)
python3 -m src.tools.validators.validation_suite --domain hdmap --inference-mode owlrl

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
DOCS_SITE_URL=http://127.0.0.1:8000/ontology-management-base make docs-serve

# Update catalogs after artifact changes
python3 -m src.tools.utils.registry_updater
```

**Installed CLI entry points** (after `make setup` or `pip install -e .`):
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
3. **check-data-conformance** — SHACL validation of instance data
4. **check-failing-tests** — Invalid data in `tests/data/{domain}/invalid/` fails as expected, matched against `.expected` files (domain mode only)

**SHACL conformance detail** (check 3 — the most complex path):
Load JSON-LD data → extract `@type` IRIs → discover matching SHACL shapes via catalog → load OWL+SHACL graphs → resolve `did:web:` fixture IRIs from test catalog → apply RDFS inference → run pyshacl

### W3ID Ontology Namespaces

Two coexisting W3ID IRI namespaces resolve to GitHub Pages (`ascs-ev.github.io/ontology-management-base/w3id/...`):

| Namespace | Pattern | Status |
|-----------|---------|--------|
| **ASCS-eV** | `w3id.org/ascs-ev/envited-x/{domain}/v{n}` | Active — new domains use this |
| **Gaia-X4PLC-AAD** | `w3id.org/gaia-x4plcaad/ontologies/{domain}/v{n}` | Legacy — migrate to ASCS-eV on next version bump |

**Migration policy:** When bumping a `gaia-x4plcaad` ontology's version, change its IRI to `ascs-ev/envited-x/{domain}/v{n+1}` and add `owl:priorVersion` pointing to the old IRI. Old version IRIs continue resolving permanently via w3id redirects.

W3ID redirect rules live in the `submodules/w3id.org/` submodule (`gaia-x4plcaad/.htaccess` and `ascs-ev/envited-x/.htaccess`).

### Pre-commit Hooks

Auto-triggered on relevant file changes (configured in `.pre-commit-config.yaml`):
- **black / isort / flake8** — Python formatting and linting
- **jsonld-lint / turtle-lint** — Syntax validation for `.json`/`.jsonld`/`.ttl` files
- **update-registry** — Regenerates `artifacts/catalog-v001.xml` when artifact files change
- **update-properties** — Regenerates `PROPERTIES.md` documentation
- **update-context** — Regenerates `.context.jsonld` files from OWL+SHACL definitions
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

## Return Codes

```
0       SUCCESS
1       GENERAL_ERROR
10      SYNTAX_ERROR
101     JSON_SYNTAX_ERROR
102     TURTLE_SYNTAX_ERROR
200     COHERENCE_ERROR
201     MISSING_TARGET_CLASS
210     CONFORMANCE_ERROR
211     SHACL_VIOLATION
99      MISSING_DEPENDENCY
100     SKIPPED
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

## Test Structure

```
tests/
├── unit/              # Unit tests per module (core/, utils/, validators/)
├── integration/       # Cross-module integration tests
├── data/              # Test instance data per domain
│   └── {domain}/
│       ├── valid/     # Instances that must pass SHACL validation
│       └── invalid/   # Instances that must fail (with .expected files)
├── fixtures/          # Shared RDF fixtures (mock did:web: references)
├── catalog-v001.xml   # Test catalog for fixture resolution
└── conftest.py        # Shared pytest fixtures (resolver, tmp_path helpers)
```

Modules also have `_run_tests()` functions for self-testing: `python3 -m src.tools.utils.file_collector --test`

## Coding Conventions

- **Python 3.12+** with type hints on public APIs
- **pathlib.Path** (never `os.path`)
- **Centralized logging** via `get_logger(__name__)`; reserve `print()` for final user output
- **Fail fast** — raise specific exceptions, no silent `None` returns
- **Test naming** — `test_{function}_{scenario}_{expected}`
- **Import order** — stdlib, third-party, local core, local utils
- **Path display** — use `normalize_path_for_display()` to avoid leaking absolute paths in output
- **Conventional commits** — short imperative subjects prefixed with `feat:`, `fix:`, `docs:`, or scoped like `feat(ontology): ...`

## Git Commit Policy

**STRICT REQUIREMENTS:**

- **Always sign commits** with `-s -S` flags (Signed-off-by + GPG signature)
- **Never include AI attribution** — no `Co-Authored-By`, `Generated-By`, or similar headers mentioning AI assistants (Claude, Copilot, ChatGPT, etc.)
- **Author must be the human developer** — use `carlo.van-driesten@bmw.de` or appropriate human email
- **No AI tool names in commit messages** — do not mention that code was generated or assisted by AI

Example commit command:
```bash
git commit -s -S -m "feat: add new feature"
```

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

When making changes to the codebase, always create/update these files in `.playground/` (gitignored):

| File | Purpose |
|------|---------|
| `.playground/commit-message.md` | Conventional commit message with bullet points, ready for copy-paste into `git commit -s -S` |
| `.playground/pr-description.md` | PR description following `.github/pull_request_template.md` |

**When instructed to prepare a commit or PR, do not commit directly.** Instead, create these files for human review. The operator will either:
- Use them to manually commit/push and create a PR, or
- Use automated tooling with signed commits (`git commit -s -S`)

Update both files **before** presenting the final result to the user. If a session involves multiple rounds of changes, keep these files in sync with the cumulative state.

## Common Mistakes to Avoid

- Bypassing catalogs with direct filesystem scanning in validators
- Using `file_collector.py` outside of `registry_updater.py`
- Using `os.path` instead of `pathlib.Path`
- Silent `None` returns instead of raising exceptions
- Using `print()` for internal progress (use `logger`)
- Leaking absolute paths in output (use `normalize_path_for_display`)
