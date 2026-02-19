# Makefile for Ontology Management Base
# Build command center for common development tasks

VENV := .venv

# Use venv if it exists, otherwise use system python
ifneq ($(wildcard $(VENV)/bin/python3),)
    PYTHON := $(VENV)/bin/python3
    PIP := $(VENV)/bin/pip
    PRECOMMIT := $(VENV)/bin/pre-commit
    PYTEST := $(VENV)/bin/pytest
else
    PYTHON := python3
    PIP := python3 -m pip
    PRECOMMIT := pre-commit
    PYTEST := pytest
endif

# Check if dev environment is set up
define check_dev_setup
	@if [ ! -d "$(VENV)" ]; then \
		echo ""; \
		echo "❌ Development environment not set up."; \
		echo ""; \
		echo "Please run first:"; \
		echo "  make setup"; \
		echo ""; \
		exit 1; \
	fi
	@if ! $(PYTHON) -c "import pre_commit" 2>/dev/null; then \
		echo ""; \
		echo "❌ Dev dependencies not installed."; \
		echo ""; \
		echo "Please run:"; \
		echo "  source $(VENV)/bin/activate"; \
		echo "  make install-dev"; \
		echo ""; \
		exit 1; \
	fi
endef

.PHONY: all setup install install-dev lint format test test-cov docs clean help

# Default target
all: lint test

# Setup: create venv and install dev dependencies
setup: $(VENV)/bin/activate
$(VENV)/bin/activate:
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev]"
	@$(PYTHON) -m pre_commit install
	@echo ""
	@echo "✅ Setup complete. Activate with: source $(VENV)/bin/activate"

# Installation targets
install:
	@$(PIP) install -e .

install-dev:
	@$(PIP) install -e ".[dev]"
	@$(PYTHON) -m pre_commit install

# Linting and formatting
lint:
	$(call check_dev_setup)
	@$(PYTHON) -m pre_commit run --all-files

format:
	$(call check_dev_setup)
	@$(PYTHON) -m black src/
	@$(PYTHON) -m isort src/

# Testing targets
test: test-check-syntax test-check-artifact-coherence test-check-data-conformance test-failing

test-check-syntax:
	@$(PYTHON) -m src.tools.validators.validation_suite --run check-syntax

test-check-artifact-coherence:
	@$(PYTHON) -m src.tools.validators.validation_suite --run check-artifact-coherence

test-check-data-conformance:
	@$(PYTHON) -m src.tools.validators.validation_suite --run check-data-conformance

test-failing:
	@$(PYTHON) -m src.tools.validators.validation_suite --run check-failing-tests

test-cov:
	$(call check_dev_setup)
	@$(PYTEST) tests/ --cov=src --cov-report=html --cov-report=term

# Test specific domain
test-domain:
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make test-domain DOMAIN=hdmap"; \
		exit 1; \
	fi
	@$(PYTHON) -m src.tools.validators.validation_suite --run all --domain $(DOMAIN)

# Documentation targets
docs-generate:
	@$(PYTHON) -m src.tools.utils.properties_updater

docs-serve:
	@mkdocs serve

docs-build:
	@mkdocs build

# Registry management
registry-update:
	@if [ -z "$(TAG)" ]; then \
		$(PYTHON) -m src.tools.utils.registry_updater --release-tag main; \
	else \
		$(PYTHON) -m src.tools.utils.registry_updater --release-tag $(TAG); \
	fi

# Cleaning
clean:
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ .mypy_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned"

clean-cache:
	@rm -f .ontology_iri_cache.json
	@rm -f .repo_registry_cache.json
	@echo "✅ Cache cleared"

# Help
help:
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
