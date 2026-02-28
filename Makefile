# Makefile for Ontology Management Base
# Build command center for common development tasks

# Allow parent makefiles to override the venv path/tooling.
VENV ?= .venv

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

# Check if dev environment is set up
define check_dev_setup
	@if [ ! -f "$(PYTHON)" ]; then \
		echo ""; \
		echo "❌ Development environment not set up."; \
		echo ""; \
		echo "Please run first:"; \
		echo "  make setup"; \
		echo ""; \
		exit 1; \
	fi
	@if ! "$(PYTHON)" -c "import pre_commit, rdflib, pyshacl" 2>/dev/null; then \
		echo ""; \
		echo "❌ Dev dependencies not installed."; \
		echo ""; \
		echo "Please run:"; \
		echo "  make setup"; \
		echo ""; \
		exit 1; \
	fi
endef

.PHONY: all setup install install-dev lint format test test-check-syntax test-check-artifact-coherence test-check-data-conformance test-failing test-cov test-domain docs-generate docs-serve docs-build registry-update clean clean-cache help

# Default target
all: lint test

# Setup: create venv and install dev dependencies
# Uses Make's dependency system for bootstrapping; validates deps are importable.
setup: $(ACTIVATE_SCRIPT)
	@if ! "$(PYTHON)" -c "import pre_commit, rdflib, pyshacl" >/dev/null 2>&1; then \
		echo "🔧 Dependencies missing; reinstalling..."; \
		"$(PYTHON)" -m pip install -e ".[dev]"; \
		"$(PYTHON)" -m pre_commit install; \
	fi
	@echo "🔧 Setting up ontology-management-base..."
	@echo "✅ Python virtual environment and dependencies are ready at $(VENV)"
	@echo ""
	@echo "✅ ontology-management-base setup complete. Activate with: source $(ACTIVATE_SCRIPT)"

$(PYTHON):
	@echo "🔧 Creating Python virtual environment at $(VENV)..."
	@"$(BOOTSTRAP_PYTHON)" -m venv "$(VENV)"
	@"$(PYTHON)" -m pip install --upgrade pip
	@echo "✅ Python virtual environment ready"

$(ACTIVATE_SCRIPT): $(PYTHON)
	@echo "🔧 Installing ontology-management-base Python dependencies..."
	@"$(PYTHON)" -m pip install -e ".[dev]"
	@"$(PYTHON)" -m pre_commit install
	@touch "$(ACTIVATE_SCRIPT)"
	@echo "✅ Python dependencies installed"

# Installation targets
install: $(PYTHON)
	@echo "🔧 Installing ontology-management-base package..."
	@"$(PYTHON)" -m pip install -e .
	@echo "✅ Package installation complete"

install-dev: $(PYTHON)
	@echo "🔧 Installing ontology-management-base development dependencies..."
	@"$(PYTHON)" -m pip install -e ".[dev]"
	@"$(PYTHON)" -m pre_commit install
	@echo "✅ Development dependencies installed"

# Linting and formatting
lint:
	$(call check_dev_setup)
	@echo "🔧 Running pre-commit checks..."
	@"$(PYTHON)" -m pre_commit run --all-files
	@echo "✅ Pre-commit checks complete"

format:
	$(call check_dev_setup)
	@echo "🔧 Formatting Python code..."
	@"$(PYTHON)" -m black src/
	@"$(PYTHON)" -m isort src/
	@echo "✅ Python formatting complete"

# Testing targets
test:
	$(call check_dev_setup)
	@echo "🔧 Running ontology-management-base validation test suite..."
	@"$(MAKE)" --no-print-directory test-check-syntax
	@"$(MAKE)" --no-print-directory test-check-artifact-coherence
	@"$(MAKE)" --no-print-directory test-check-data-conformance
	@"$(MAKE)" --no-print-directory test-failing
	@echo "✅ Validation test suite complete"

test-check-syntax:
	@echo "🔧 Running check-syntax..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-syntax
	@echo "✅ check-syntax complete"

test-check-artifact-coherence:
	@echo "🔧 Running check-artifact-coherence..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-artifact-coherence
	@echo "✅ check-artifact-coherence complete"

test-check-data-conformance:
	@echo "🔧 Running check-data-conformance..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-data-conformance
	@echo "✅ check-data-conformance complete"

test-failing:
	@echo "🔧 Running check-failing-tests..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run check-failing-tests
	@echo "✅ check-failing-tests complete"

test-cov:
	$(call check_dev_setup)
	@echo "🔧 Running unit tests with coverage..."
	@"$(PYTHON)" -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "✅ Coverage run complete"

# Test specific domain
test-domain:
	$(call check_dev_setup)
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make test-domain DOMAIN=hdmap"; \
		exit 1; \
	fi
	@echo "🔧 Running full validation suite for domain: $(DOMAIN)..."
	@"$(PYTHON)" -m src.tools.validators.validation_suite --run all --domain $(DOMAIN)
	@echo "✅ Domain validation complete"

# Documentation targets
docs-generate:
	$(call check_dev_setup)
	@echo "🔧 Generating documentation assets..."
	@"$(PYTHON)" -m src.tools.utils.properties_updater
	@echo "✅ Documentation assets generated"

docs-serve:
	$(call check_dev_setup)
	@echo "🔧 Starting MkDocs development server..."
	@"$(PYTHON)" -m mkdocs serve

docs-build:
	$(call check_dev_setup)
	@echo "🔧 Building MkDocs site..."
	@"$(PYTHON)" -m mkdocs build
	@echo "✅ Documentation build complete"

# Registry management
registry-update:
	$(call check_dev_setup)
	@echo "🔧 Updating ontology registry..."
	@if [ -z "$(TAG)" ]; then \
		"$(PYTHON)" -m src.tools.utils.registry_updater --release-tag main; \
	else \
		"$(PYTHON)" -m src.tools.utils.registry_updater --release-tag $(TAG); \
	fi
	@echo "✅ Registry update complete"

# Cleaning
clean:
	@echo "🔧 Cleaning generated files and caches..."
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ .mypy_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned"

clean-cache:
	@echo "🔧 Clearing local cache files..."
	@rm -f .ontology_iri_cache.json
	@rm -f .repo_registry_cache.json
	@echo "✅ Cache cleared"

# Help
help:
	@echo "🔧 Showing available commands..."
	@echo "Ontology Management Base - Available Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make setup          - Create venv and install dev dependencies"
	@echo "  make install        - Install package (user mode)"
	@echo "  make install-dev    - Install with dev dependencies + pre-commit"
	@echo ""
	@echo "Linting:"
	@echo "  make lint           - Run pre-commit checks"
	@echo "  make format         - Format code with black/isort"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all validation tests"
	@echo "  make test-cov       - Run unit tests with coverage report"
	@echo "  make test-check-syntax           - Run syntax checks only"
	@echo "  make test-check-data-conformance - Run SHACL validation only"
	@echo "  make test-domain DOMAIN=hdmap   - Test specific domain"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs-generate  - Generate PROPERTIES.md files"
	@echo "  make docs-serve     - Start local docs server"
	@echo "  make docs-build     - Build static docs site"
	@echo ""
	@echo "Registry:"
	@echo "  make registry-update         - Update registry (main branch)"
	@echo "  make registry-update TAG=v1  - Update registry with tag"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean          - Remove build artifacts and caches"
	@echo "  make clean-cache    - Remove cache files"
