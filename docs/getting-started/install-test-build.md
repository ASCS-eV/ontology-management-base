# Install, Test, Build

This page covers the full setup flow for users and contributors.

## Requirements

- **Python ≥ 3.12** (required — older versions will fail with syntax errors)
- **Git**
- **uv** ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **just** ([installation packages](https://just.systems/man/en/packages.html))

## Install

```bash
git clone https://github.com/ASCS-eV/ontology-management-base.git
cd ontology-management-base

git submodule update --init --recursive

# One-command setup (creates .venv, installs dev deps, installs pre-commit hooks)
just setup
```

No activation is required for `just` recipes; they run through `uv run`. Activate the environment only for direct Python or pip commands:

```bash
# Linux / macOS / Git Bash
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

## VS Code: Auto-activate virtual environment

Install the Python extension, then select the interpreter for this workspace so terminals auto-activate it.

1. Command Palette → "Python: Select Interpreter" → choose `.venv`.
2. Ensure these settings are enabled:

```json
{
  "python.terminal.activateEnvironment": true,
  "python.venvFolders": [".venv", "venv", "env"]
}
```

## Test

Run the full validation suite:

```bash
just test
```

Run a single domain:

```bash
just test-domain hdmap
```

## Build Documentation

Build the site:

```bash
just docs-build
```

To preview locally (auto-generates docs assets):

```bash
DOCS_SITE_URL=http://127.0.0.1:8000/ontology-management-base just docs-serve
```

Notes:

Hook flow (via `hooks/copy_artifacts.py`):

1. The hook runs `properties_updater` and `class_page_generator` (DOCS_SITE_URL is optional and only affects local diagram links).
2. `properties_updater` writes tracked `artifacts/<domain>/PROPERTIES.md`, generates `docs/ontologies/properties/<domain>.md` (ignored by git), builds the `docs/ontologies/properties.md` domains overview, and refreshes `docs/ontologies/catalog.md`.
3. `class_page_generator` writes `docs/ontologies/classes/<domain>/*.md` and uses `DOCS_SITE_URL` to build local diagram links.
4. The hook copies `artifacts/<domain>/` into `docs/artifacts/<domain>/<versionInfo>/` and adds example instances from `tests/data/`.

## Common Troubleshooting

- If `pyshacl` is missing, install dev dependencies.
- If catalogs are missing, run the registry updater:

```bash
python3 -m omb.utils.registry_updater
```
