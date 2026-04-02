# Makefile for Ontology Management Base
# Build command center for common development tasks

# Allow parent makefiles to override the venv path/tooling.
VENV ?= .venv

# CI detection — in CI, use system Python directly (no venv creation).
# GitHub Actions sets CI=true as an environment variable.
ifdef CI
    PYTHON ?= python3
    PIP := $(PYTHON) -m pip
    PRECOMMIT := $(PYTHON) -m pre_commit
    ACTIVATE_HINT := (CI mode — no venv)
    VENV_BIN := $(dir $(shell which python3))
else
    # OS detection for cross-platform support (Windows vs Unix)
    ifeq ($(OS),Windows_NT)
        # Windows (including Git Bash, MSYS2, MINGW)
        VENV_BIN := $(VENV)/Scripts
        PYTHON ?= $(VENV_BIN)/python.exe
        BOOTSTRAP_PYTHON ?= python
        ACTIVATE_SCRIPT := $(VENV_BIN)/activate
    else
        # Unix (Linux, macOS)
        VENV_BIN := $(VENV)/bin
        PYTHON ?= $(VENV_BIN)/python3
        BOOTSTRAP_PYTHON ?= python3
        ACTIVATE_SCRIPT := $(VENV_BIN)/activate
    endif
    PIP := "$(PYTHON)" -m pip
    PRECOMMIT := "$(PYTHON)" -m pre_commit
    ACTIVATE_HINT := Activate with: source $(ACTIVATE_SCRIPT)
endif

# Absolute path to Python — needed after cd into subdirectories
PYTHON_ABS := $(abspath $(PYTHON))

# Check if dev environment is set up
define check_dev_setup
	@if [ -z "$$CI" ] && [ ! -f "$(PYTHON)" ]; then \
		echo ""; \
		echo "[ERR] Development environment not set up."; \
		echo ""; \
		echo "Please run first:"; \
		echo "  make setup"; \
		echo ""; \
		exit 1; \
	fi
	@if ! "$(PYTHON)" -c "import pre_commit, rdflib, pyshacl" 2>/dev/null; then \
		echo ""; \
		echo "[ERR] Dev dependencies not installed."; \
		echo ""; \
		echo "Please run:"; \
		echo "  make setup"; \
		echo ""; \
		exit 1; \
	fi
endef

# LinkML generators
GEN_OWL := $(VENV_BIN)/gen-owl
GEN_SHACL := $(VENV_BIN)/gen-shacl
GEN_JSONLD_CONTEXT := $(VENV_BIN)/gen-jsonld-context

# LinkML domains — add new domains here
LINKML_DOMAINS := openlabel-v2
GX_SUBMODULE_DIR := submodules/service-characteristics
GX_ARTIFACTS_DIR := artifacts/gx
GX_UPDATE_SCRIPT := $(GX_ARTIFACTS_DIR)/update-from-submodule.sh

.PHONY: all setup install lint format test validate generate docs registry clean help \
	_help_general _help_install _help_test _help_docs _help_registry _help_clean \
	_help_generate _install_default _install_dev \
	_generate_default _generate_gx \
	_test_default _test_syntax _test_artifact_coherence _test_data_conformance _test_failing _test_cov _test_domain \
	_docs_generate _docs_serve _docs_build \
	_registry_update _clean_default _clean_cache

GROUPED_COMMANDS := install generate test validate docs registry clean
PRIMARY_GOAL := $(firstword $(MAKECMDGOALS))

ifneq ($(filter $(PRIMARY_GOAL),$(GROUPED_COMMANDS)),)
help:
	@:

%:
	@:
else
help:
	@"$(MAKE)" --no-print-directory _help_general
endif

# Default target
all: lint test

# Setup: create venv and install dev dependencies
# Uses Make's dependency system for bootstrapping; validates deps are importable.
ifdef CI
setup:
	@echo "[INFO] CI mode — installing dependencies without venv..."
	@$(PIP) install -e ".[dev]"
	@echo "[OK] ontology-management-base setup complete (CI mode)"
else
setup: $(ACTIVATE_SCRIPT)
	@if ! "$(PYTHON)" -c "import pre_commit, rdflib, pyshacl" >/dev/null 2>&1; then \
		echo "[INFO] Dependencies missing; reinstalling..."; \
		$(PIP) install -e ".[dev]"; \
		$(PRECOMMIT) install; \
	fi
	@echo "[INFO] Setting up ontology-management-base..."
	@echo "[OK] Python virtual environment and dependencies are ready at $(VENV)"
	@echo ""
	@echo "[OK] ontology-management-base setup complete. $(ACTIVATE_HINT)"
endif

ifndef CI
$(PYTHON):
	@echo "[INFO] Creating Python virtual environment at $(VENV)..."
	@"$(BOOTSTRAP_PYTHON)" -m venv "$(VENV)"
	@"$(PYTHON)" -m pip install --upgrade pip
	@echo "[OK] Python virtual environment ready"

$(ACTIVATE_SCRIPT): $(PYTHON)
	@echo "[INFO] Installing ontology-management-base Python dependencies..."
	@$(PIP) install -e ".[dev]"
	@$(PRECOMMIT) install
	@touch "$(ACTIVATE_SCRIPT)"
	@echo "[OK] Python dependencies installed"
endif

# Installation targets
install:
	@set -- $(filter-out $@,$(MAKECMDGOALS)); \
	subcommand="$${1:-default}"; \
	if [ "$$#" -gt 1 ]; then \
		echo "ERROR: Too many subcommands for 'make install': $(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Run 'make install help' for available options."; \
		exit 1; \
	fi; \
	case "$$subcommand" in \
		default) "$(MAKE)" --no-print-directory _install_default ;; \
		dev) "$(MAKE)" --no-print-directory _install_dev ;; \
		help) "$(MAKE)" --no-print-directory _help_install ;; \
		*) echo "ERROR: Unknown install subcommand '$$subcommand'"; echo "Run 'make install help' for available options."; exit 1 ;; \
	esac

ifdef CI
_install_default:
	@echo "[INFO] Installing ontology-management-base package..."
	@$(PIP) install -e .
	@echo "[OK] Package installation complete"

_install_dev:
	@echo "[INFO] Installing ontology-management-base development dependencies..."
	@$(PIP) install -e ".[dev]"
	@echo "[OK] Development dependencies installed"
else
_install_default: $(PYTHON)
	@echo "[INFO] Installing ontology-management-base package..."
	@$(PIP) install -e .
	@echo "[OK] Package installation complete"

_install_dev: $(PYTHON)
	@echo "[INFO] Installing ontology-management-base development dependencies..."
	@$(PIP) install -e ".[dev]"
	@$(PRECOMMIT) install
	@echo "[OK] Development dependencies installed"
endif

# Linting and formatting
lint:
	$(call check_dev_setup)
	@echo "[INFO] Running pre-commit checks..."
	@$(PRECOMMIT) run --all-files
	@echo "[OK] Pre-commit checks complete"

format:
	$(call check_dev_setup)
	@echo "[INFO] Formatting Python code..."
	@"$(PYTHON)" -m ruff check --fix src/
	@"$(PYTHON)" -m ruff format src/
	@echo "[OK] Python formatting complete"

generate:
	@set -- $(filter-out $@,$(MAKECMDGOALS)); \
	subcommand="$${1:-default}"; \
	if [ "$$#" -gt 1 ]; then \
		echo "ERROR: Too many subcommands for 'make generate': $(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Run 'make generate help' for available options."; \
		exit 1; \
	fi; \
	case "$$subcommand" in \
		default) "$(MAKE)" --no-print-directory _generate_default DOMAIN="$(DOMAIN)" ;; \
		gx) "$(MAKE)" --no-print-directory _generate_gx GX_REF="$(GX_REF)" ;; \
		help) "$(MAKE)" --no-print-directory _help_generate ;; \
		*) echo "ERROR: Unknown generate subcommand '$$subcommand'"; echo "Run 'make generate help' for available options."; exit 1 ;; \
	esac

# LinkML generation targets
_generate_default:
	$(call check_dev_setup)
	@echo "[INFO] Generating artifacts from LinkML schemas..."
	@if [ -n "$(DOMAIN)" ]; then \
		DOMAINS_TO_BUILD="$(DOMAIN)"; \
	else \
		DOMAINS_TO_BUILD="$(LINKML_DOMAINS)"; \
	fi; \
	for domain in $$DOMAINS_TO_BUILD; do \
		echo "  Processing $$domain..."; \
		mkdir -p artifacts/$$domain; \
		"$(GEN_OWL)" --deterministic --normalize-prefixes --no-metadata --ontology-uri-suffix "" linkml/$$domain/$$domain.yaml > artifacts/$$domain/$$domain.owl.ttl 2>/dev/null; \
		"$(GEN_SHACL)" --deterministic --normalize-prefixes --no-metadata linkml/$$domain/$$domain.yaml > artifacts/$$domain/$$domain.shacl.ttl 2>/dev/null; \
		"$(GEN_JSONLD_CONTEXT)" --deterministic --normalize-prefixes --no-metadata --exclude-external-imports --xsd-anyuri-as-iri linkml/$$domain/$$domain.yaml > artifacts/$$domain/$$domain.context.jsonld 2>/dev/null; \
	done
	@echo "[OK] Artifacts generated"

_generate_gx:
	$(call check_dev_setup)
	@if [ ! -d "$(GX_SUBMODULE_DIR)" ]; then \
		echo "[ERR] Gaia-X submodule not found at $(GX_SUBMODULE_DIR)"; \
		echo "Run: git submodule update --init --recursive"; \
		exit 1; \
	fi
	@echo "[INFO] Regenerating Gaia-X artifacts from $(GX_SUBMODULE_DIR)..."
	@if [ -n "$(GX_REF)" ]; then \
		PATH="$(abspath $(VENV_BIN)):$$PATH" bash "$(GX_UPDATE_SCRIPT)" "$(GX_REF)"; \
	else \
		PATH="$(abspath $(VENV_BIN)):$$PATH" bash "$(GX_UPDATE_SCRIPT)"; \
	fi
	@echo "[OK] Gaia-X artifacts refreshed"

# Testing targets
test:
	@set -- $(filter-out $@,$(MAKECMDGOALS)); \
	subcommand="$${1:-default}"; \
	if [ "$$#" -gt 1 ]; then \
		echo "ERROR: Too many subcommands for 'make test': $(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Run 'make test help' for available options."; \
		exit 1; \
	fi; \
	case "$$subcommand" in \
		default) "$(MAKE)" --no-print-directory _test_default ;; \
		syntax) "$(MAKE)" --no-print-directory _test_syntax ;; \
		artifact-coherence) "$(MAKE)" --no-print-directory _test_artifact_coherence ;; \
		data-conformance) "$(MAKE)" --no-print-directory _test_data_conformance ;; \
		failing) "$(MAKE)" --no-print-directory _test_failing ;; \
		cov) "$(MAKE)" --no-print-directory _test_cov ;; \
		domain) "$(MAKE)" --no-print-directory _test_domain ;; \
		help) "$(MAKE)" --no-print-directory _help_test ;; \
		*) echo "ERROR: Unknown test subcommand '$$subcommand'"; echo "Run 'make test help' for available options."; exit 1 ;; \
	esac

_test_default:
	$(call check_dev_setup)
	@echo "[INFO] Running ontology-management-base validation test suite..."
	@"$(MAKE)" --no-print-directory _test_syntax
	@"$(MAKE)" --no-print-directory _test_artifact_coherence
	@"$(MAKE)" --no-print-directory _test_data_conformance
	@"$(MAKE)" --no-print-directory _test_failing
	@echo "[OK] Validation test suite complete"

_test_syntax:
	@echo "[INFO] Running check-syntax..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-syntax
	@echo "[OK] check-syntax complete"

_test_artifact_coherence:
	@echo "[INFO] Running check-artifact-coherence..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-artifact-coherence
	@echo "[OK] check-artifact-coherence complete"

_test_data_conformance:
	@echo "[INFO] Running check-data-conformance..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-data-conformance
	@echo "[OK] check-data-conformance complete"

_test_failing:
	@echo "[INFO] Running check-failing-tests..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-failing-tests
	@echo "[OK] check-failing-tests complete"

_test_cov:
	$(call check_dev_setup)
	@echo "[INFO] Running unit tests with coverage..."
	@"$(PYTHON)" -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "[OK] Coverage run complete"

# Test specific domain
_test_domain:
	$(call check_dev_setup)
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make test domain DOMAIN=hdmap"; \
		exit 1; \
	fi
	@echo "[INFO] Running full validation suite for domain: $(DOMAIN)..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run all --domain "$(DOMAIN)"
	@echo "[OK] Domain validation complete"

# Validate target — runs the validation suite with optional ARGS passthrough.
# Usage: make validate ARGS="--run check-data-conformance --domain hdmap"
validate:
	$(call check_dev_setup)
	@echo "[INFO] Running validation suite..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite $(ARGS)
	@echo "[OK] Validation complete"

# Documentation targets
docs:
	@set -- $(filter-out $@,$(MAKECMDGOALS)); \
	subcommand="$${1:-help}"; \
	if [ "$$#" -gt 1 ]; then \
		echo "ERROR: Too many subcommands for 'make docs': $(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Run 'make docs help' for available options."; \
		exit 1; \
	fi; \
	case "$$subcommand" in \
		generate) "$(MAKE)" --no-print-directory _docs_generate ;; \
		serve) "$(MAKE)" --no-print-directory _docs_serve ;; \
		build) "$(MAKE)" --no-print-directory _docs_build ;; \
		help|default) "$(MAKE)" --no-print-directory _help_docs ;; \
		*) echo "ERROR: Unknown docs subcommand '$$subcommand'"; echo "Run 'make docs help' for available options."; exit 1 ;; \
	esac

_docs_generate:
	$(call check_dev_setup)
	@echo "[INFO] Generating documentation assets..."
	@"$(PYTHON)" -m src.tools.utils.properties_updater
	@echo "[OK] Documentation assets generated"

_docs_serve:
	$(call check_dev_setup)
	@echo "[INFO] Starting MkDocs development server..."
	@"$(PYTHON)" -m mkdocs serve

_docs_build:
	$(call check_dev_setup)
	@echo "[INFO] Building MkDocs site..."
	@"$(PYTHON)" -m mkdocs build
	@echo "[OK] Documentation build complete"

# Registry management
registry:
	@set -- $(filter-out $@,$(MAKECMDGOALS)); \
	subcommand="$${1:-help}"; \
	if [ "$$#" -gt 1 ]; then \
		echo "ERROR: Too many subcommands for 'make registry': $(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Run 'make registry help' for available options."; \
		exit 1; \
	fi; \
	case "$$subcommand" in \
		update) "$(MAKE)" --no-print-directory _registry_update TAG="$(TAG)" ;; \
		help|default) "$(MAKE)" --no-print-directory _help_registry ;; \
		*) echo "ERROR: Unknown registry subcommand '$$subcommand'"; echo "Run 'make registry help' for available options."; exit 1 ;; \
	esac

_registry_update:
	$(call check_dev_setup)
	@TAG_VALUE="$(TAG)"; \
	if [ -z "$$TAG_VALUE" ]; then \
		TAG_VALUE="v$$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)"; \
	fi; \
	echo "[INFO] Updating ontology registry (tag: $$TAG_VALUE)..."; \
	"$(PYTHON)" -m src.tools.utils.registry_updater --release-tag "$$TAG_VALUE"
	@echo "[OK] Registry update complete"

# Cleaning
clean:
	@set -- $(filter-out $@,$(MAKECMDGOALS)); \
	subcommand="$${1:-default}"; \
	if [ "$$#" -gt 1 ]; then \
		echo "ERROR: Too many subcommands for 'make clean': $(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Run 'make clean help' for available options."; \
		exit 1; \
	fi; \
	case "$$subcommand" in \
		default) "$(MAKE)" --no-print-directory _clean_default ;; \
		cache) "$(MAKE)" --no-print-directory _clean_cache ;; \
		help) "$(MAKE)" --no-print-directory _help_clean ;; \
		*) echo "ERROR: Unknown clean subcommand '$$subcommand'"; echo "Run 'make clean help' for available options."; exit 1 ;; \
	esac

_clean_default:
	@echo "[INFO] Cleaning generated files and caches..."
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ .mypy_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "[OK] Cleaned"

_clean_cache:
	@echo "[INFO] Clearing local cache files..."
	@rm -f .ontology_iri_cache.json
	@rm -f .repo_registry_cache.json
	@echo "[OK] Cache cleared"

# Help
_help_general:
	@echo "[INFO] Showing available commands..."
	@echo "Ontology Management Base - Available Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make setup          - Create venv and install dev dependencies"
	@echo "  make install        - Install package (user mode)"
	@echo "  make install help   - Show install subcommands"
	@echo ""
	@echo "Linting:"
	@echo "  make lint           - Run pre-commit checks"
	@echo "  make format         - Format code with ruff"
	@echo ""
	@echo "LinkML:"
	@echo "  make generate                     - Generate OWL/SHACL/context from all OMB LinkML schemas"
	@echo "  make generate DOMAIN=openlabel-v2 - Generate for a specific OMB domain"
	@echo "  make generate gx                  - Build and sync Gaia-X artifacts from service-characteristics"
	@echo "  make generate help                - Show generate subcommands"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all validation tests"
	@echo "  make test help     - Show test subcommands"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs help     - Show docs subcommands"
	@echo ""
	@echo "Registry:"
	@echo "  make registry help - Show registry subcommands"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean         - Remove build artifacts and caches"
	@echo "  make clean help    - Show clean subcommands"

_help_install:
	@echo "Install subcommands:"
	@echo "  make install      - Install package (user mode)"
	@echo "  make install dev  - Install with dev dependencies + pre-commit"

_help_generate:
	@echo "Generate subcommands:"
	@echo "  make generate                     - Generate OWL/SHACL/context from all OMB LinkML schemas"
	@echo "  make generate DOMAIN=openlabel-v2 - Generate for a specific OMB domain"
	@echo "  make generate gx                  - Build and sync Gaia-X artifacts from service-characteristics"
	@echo "  make generate gx GX_REF=25.12     - Check out a specific Gaia-X ref before generating"

_help_test:
	@echo "Test subcommands:"
	@echo "  make test                     - Run all validation tests"
	@echo "  make test syntax              - Run syntax checks only"
	@echo "  make test artifact-coherence  - Run artifact coherence checks"
	@echo "  make test data-conformance    - Run SHACL validation only"
	@echo "  make test failing             - Run failing-tests checks"
	@echo "  make test cov                 - Run unit tests with coverage report"
	@echo "  make test domain DOMAIN=hdmap - Test a specific domain"

_help_docs:
	@echo "Docs subcommands:"
	@echo "  make docs generate  - Generate PROPERTIES.md files"
	@echo "  make docs serve     - Start local docs server"
	@echo "  make docs build     - Build static docs site"

_help_registry:
	@echo "Registry subcommands:"
	@echo "  make registry update         - Update registry (tag from pyproject.toml)"
	@echo "  make registry update TAG=v1  - Update registry with custom tag"

_help_clean:
	@echo "Clean subcommands:"
	@echo "  make clean        - Remove build artifacts and caches"
	@echo "  make clean cache  - Remove cache files"
