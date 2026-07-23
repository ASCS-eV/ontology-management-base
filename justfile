# Ontology Management Base — task runner.
#
# One command runner (replaces the old Makefile). Recipes run through `uv`, which
# creates/syncs an isolated `.venv` from pyproject.toml and fetches a compatible
# Python (>=3.12) on demand — no manual venv creation or activation needed.
#
# Quick start:
#   just setup      # create the dev environment + install pre-commit hooks
#   just --list     # see every recipe
#
# Requires `uv` (https://docs.astral.sh/uv/) and `just` (https://just.systems) on PATH.

# Run a command inside the project's dev environment. `--frozen` uses the
# committed uv.lock as-is (no re-resolution — the dev extra pins linkml from a
# git branch, which uv would otherwise re-check on every call), syncing `.venv`
# from the lock; `--extra dev` selects the dev dependencies from the locked graph.
run := "uv run --frozen --extra dev"

export PYTHONUTF8 := "1"
export PYTHONIOENCODING := "utf-8"

# LinkML domains that `just generate` builds (space-separated; add new domains here).
LINKML_DOMAINS := "openlabel-v2"

# Gaia-X artifact update script (see `just generate-gx`).
GX_UPDATE_SCRIPT := "artifacts/gx/update-from-submodule.sh"

# Default: list all recipes.
default:
    @just --list

# ===== Setup / install =====

# Create the dev environment (.venv + dev deps) and install pre-commit git hooks.
setup:
    uv sync --extra dev
    {{run}} pre-commit install
    @echo "[OK] Dev environment ready. Run recipes with: just <recipe>"

# Install the package with runtime dependencies only.
install:
    uv sync

# Install the package with dev dependencies.
install-dev:
    uv sync --extra dev

# ===== Lint / format =====

# Run all pre-commit checks across the whole repo (the CI 'Standards & Syntax' gate).
lint:
    {{run}} pre-commit run --all-files

# Auto-format Python with ruff (check --fix, then format).
format:
    {{run}} ruff check --fix omb/
    {{run}} ruff format omb/

# ===== Generate artifacts (OWL / SHACL / JSON-LD context) =====

# Generate artifacts for every OMB LinkML domain. MUST stay byte-identical to the
# committed artifacts/ (CI fails on any diff) — the flags + `tr`/`sed` cleanup below
# are load-bearing; change them only alongside a reviewed artifact re-record.
generate:
    #!/usr/bin/env bash
    set -euo pipefail
    for domain in {{LINKML_DOMAINS}}; do
        echo "  Processing $domain..."
        mkdir -p "artifacts/$domain"
        {{run}} gen-owl --deterministic --normalize-prefixes --xsd-anyuri-as-iri --no-metadata --default-language en --ontology-uri-suffix "" "linkml/$domain/$domain.yaml" 2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' > "artifacts/$domain/$domain.owl.ttl"
        {{run}} gen-shacl --deterministic --normalize-prefixes --no-metadata --default-language en --message-template "{name} ({class}): {description} {comments}" "linkml/$domain/$domain.yaml" 2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' > "artifacts/$domain/$domain.shacl.ttl"
        {{run}} gen-jsonld-context --deterministic --normalize-prefixes --no-metadata --exclude-external-imports --xsd-anyuri-as-iri "linkml/$domain/$domain.yaml" 2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' > "artifacts/$domain/$domain.context.jsonld"
    done
    echo "[OK] Artifacts generated"

# Generate artifacts for a single domain, e.g. `just generate-domain openlabel-v2`.
generate-domain domain:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p "artifacts/{{domain}}"
    {{run}} gen-owl --deterministic --normalize-prefixes --xsd-anyuri-as-iri --no-metadata --default-language en --ontology-uri-suffix "" "linkml/{{domain}}/{{domain}}.yaml" 2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' > "artifacts/{{domain}}/{{domain}}.owl.ttl"
    {{run}} gen-shacl --deterministic --normalize-prefixes --no-metadata --default-language en --message-template "{name} ({class}): {description} {comments}" "linkml/{{domain}}/{{domain}}.yaml" 2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' > "artifacts/{{domain}}/{{domain}}.shacl.ttl"
    {{run}} gen-jsonld-context --deterministic --normalize-prefixes --no-metadata --exclude-external-imports --xsd-anyuri-as-iri "linkml/{{domain}}/{{domain}}.yaml" 2>/dev/null | tr -d '\r' | sed -e '${' -e '/^$/d' -e '}' > "artifacts/{{domain}}/{{domain}}.context.jsonld"
    echo "[OK] Artifacts generated for {{domain}}"

# Rebuild and sync Gaia-X artifacts from the service-characteristics submodule.
# Optional ref, e.g. `just generate-gx 25.12`.
generate-gx gx_ref="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -d "submodules/service-characteristics" ]; then
        echo "[ERR] Gaia-X submodule not found at submodules/service-characteristics" >&2
        echo "      Run: git submodule update --init --recursive" >&2
        exit 1
    fi
    {{run}} bash "{{GX_UPDATE_SCRIPT}}" {{gx_ref}}
    @echo "[OK] Gaia-X artifacts refreshed"

# ===== Validation suite =====

# Full validation suite: syntax + artifact-coherence + data-conformance + failing.
test: test-syntax test-artifact-coherence test-data-conformance test-failing
    @echo "[OK] Validation test suite complete"

# check-syntax only.
test-syntax:
    {{run}} python -m omb.validators.validation_suite --run check-syntax

# check-artifact-coherence only.
test-artifact-coherence:
    {{run}} python -m omb.validators.validation_suite --run check-artifact-coherence

# check-data-conformance (SHACL) only.
test-data-conformance:
    {{run}} python -m omb.validators.validation_suite --run check-data-conformance

# check-failing-tests (negative snapshots) only.
test-failing:
    {{run}} python -m omb.validators.validation_suite --run check-failing-tests

# Run the pytest unit suite with coverage (HTML + terminal report).
test-cov:
    {{run}} python -m pytest tests/ --cov=omb --cov-report=html --cov-report=term

# Full validation suite for a single domain, e.g. `just test-domain hdmap`.
test-domain domain:
    {{run}} python -m omb.validators.validation_suite --run all --domain "{{domain}}"

# Run the validation suite with arbitrary passthrough args (used by CI). Example:
#   just validate --run check-data-conformance --domain hdmap
validate *args:
    {{run}} python -m omb.validators.validation_suite {{args}}

# Validate a single data file or directory against the catalog, e.g.
#   just validate-file path/to/instance.json
# The file's parent dir is scanned for fixtures. Pass extra flags after the
# path (e.g. --offline, --per-resource, --strict). First-class bare-data
# (--type) support is a later workstream (W5).
validate-file path *extra:
    {{run}} python -m omb.validators.validation_suite --data-paths "{{path}}" {{extra}}

# ===== Documentation =====

# Generate PROPERTIES.md / docs assets.
docs-generate:
    {{run}} python -m omb.utils.properties_updater

# Serve the MkDocs site locally with live reload.
docs-serve:
    {{run}} python -m mkdocs serve

# Build the static MkDocs site.
docs-build:
    {{run}} python -m mkdocs build

# ===== Registry =====

# Update the ontology registry/catalog. Tag defaults to the version in pyproject.toml;
# override with `just registry-update v1.2.3`.
registry-update tag="":
    #!/usr/bin/env bash
    set -euo pipefail
    tag="{{tag}}"
    if [ -z "$tag" ]; then
        tag="v$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)"
    fi
    echo "[INFO] Updating ontology registry (tag: $tag)..."
    {{run}} python -m omb.utils.registry_updater --release-tag "$tag"
    echo "[OK] Registry update complete"

# ===== Cleaning =====

# Remove build artifacts and caches.
clean:
    #!/usr/bin/env bash
    set -euo pipefail
    rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    echo "[OK] Cleaned"

# Remove local cache files.
clean-cache:
    rm -f .ontology_iri_cache.json .repo_registry_cache.json
    @echo "[OK] Cache cleared"
