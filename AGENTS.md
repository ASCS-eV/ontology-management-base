# Repository Guidelines

## Instruction Files

Read these before making changes; they are authoritative for repo workflows.

| Topic                           | File                                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------------------ |
| Agent instructions              | [.github/copilot-instructions.md](.github/copilot-instructions.md)                         |
| Module structure & dependencies | [.github/instructions/architecture.md](.github/instructions/architecture.md)               |
| Code style & patterns           | [.github/instructions/coding-standards.md](.github/instructions/coding-standards.md)       |
| Validation pipeline             | [.github/instructions/validation-workflow.md](.github/instructions/validation-workflow.md) |
| Testing requirements            | [.github/instructions/testing.md](.github/instructions/testing.md)                         |
| Domain terminology              | [.github/instructions/glossary.md](.github/instructions/glossary.md)                       |

## Project Structure & Module Organization

- `src/tools/` is the Python codebase with layered modules: `core/` (foundations), `utils/` (catalog + graph helpers), and `validators/` (CLI validation pipeline).
- XML catalogs live in `artifacts/`, `imports/`, and `tests/`; they control discovery.
- Tests are in `tests/` with `unit/`, `integration/`, shared fixtures in `conftest.py`, and domain data in `tests/data/{domain}/`.
- Key file types include `.owl.ttl`, `.shacl.ttl`, `.context.jsonld`, and `.expected` for invalid test outputs.

## Build, Test, and Development Commands

- `make install-dev` installs dev dependencies and pre-commit hooks.
- `make lint` runs `pre-commit`; `make format` runs `black` and `isort` on `src/`.
- `python3 -m src.tools.validators.validation_suite` runs the full suite (auto-discovery). Use `--domain manifest` or `--data-paths ./file.json` for scoped runs.
- `pytest tests/` runs all tests; `pytest tests/ --cov=src/tools --cov-report=html` generates coverage reports.
- `make registry-update TAG=vX.Y.Z` updates catalogs for a release; `mkdocs serve` runs docs locally.

## Coding Style & Naming Conventions

- Python with 4-space indentation, type hints on public APIs, and module docstring headers as defined in `coding-standards.md`.
- Use `pathlib.Path` (not `os.path`), raise specific exceptions, and return `ReturnCodes` for CLI results.
- Log via `get_logger` from `src.tools.core.logging`; reserve `print()` for final user-facing output.
- Import order: stdlib, third-party, local `core`, local `utils`. Tests follow `test_{function}_{scenario}_{expected}`.

## Testing Guidelines

- Pytest is required; cover happy path, edge cases, error cases, and boundaries.
- CI expects >80% coverage for `src/tools` and the validation suite to pass.
- Invalid data tests require matching `.expected` files in `tests/data/{domain}/invalid/`.

## Architecture & Catalog Rules

- Catalog-driven architecture: validators must never scan the filesystem directly.
- `registry_updater.py` writes catalogs (and is the only place using `file_collector.py`); `registry_resolver.py` reads catalogs.
- Missing catalog entries should fail fast with clear errors; no silent fallbacks.

## Commit & Pull Request Guidelines

- Recent history favors short, imperative subjects with optional prefixes like `feat:`, `fix:`, `docs:`, or scoped forms like `feat(ontology): ...`.
- PRs should follow `.github/pull_request_template.md`: clear summary, linked issue, test evidence, and versioning/compatibility checklist items when ontology changes apply.
- **Always sign commits** with `-s -S` flags (Signed-off-by + GPG signature).
- **Never include AI attribution** in commits — no `Co-Authored-By` or similar headers mentioning AI assistants.
- **Never mention AI tools in commit messages** — do not reference that code was AI-generated or AI-assisted.
- **Author must be a human developer** with their official email address.

### Preparing Commits and Pull Requests

When instructed to prepare a commit or PR, **do not commit directly**. Instead:

1. Create files in the `.playground/` directory (already in `.gitignore`)
2. Generate two markdown files:
   - `.playground/commit-message.md` — Conventional commit message(s)
   - `.playground/pr-description.md` — PR description following `.github/pull_request_template.md`

The human operator will review these files and either:
- Use them to manually commit/push and create a PR, or
- Use automated tooling with signed commits (`git commit -s -S`)

#### Commit Message Format

```markdown
# .playground/commit-message.md

feat(ontology): add vehicle domain ontology

- Define VehicleCredential type with SHACL shapes
- Add JSON-LD context with proper prefixes
- Include valid/invalid test instances

Refs: #123
```

#### PR Description Format

Follow `.github/pull_request_template.md`:

```markdown
# .playground/pr-description.md

## Summary

Brief description of the changes.

## Changes

- List of specific changes made

## Testing

- [ ] Validation passes (`make test`)
- [ ] Pre-commit hooks pass (`make lint`)

## Related Issues

Closes #123
```
