.PHONY: help venv install install-dev uninstall clean test test-hardware test-no-hardware lint format typecheck coverage pre-commit install-pre-commit

# Python interpreter to use
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin

# Use venv binaries
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
RUFF := $(VENV_BIN)/ruff
MYPY := $(VENV_BIN)/mypy
PRE_COMMIT := $(VENV_BIN)/pre-commit

# Default target
help:
	@echo "nimbiestatemachine development commands:"
	@echo ""
	@echo "  make venv             Create virtual environment"
	@echo "  make install          Install package in development mode"
	@echo "  make install-dev      Install package with dev dependencies"
	@echo "  make uninstall        Uninstall the package"
	@echo "  make clean            Remove build artifacts and cache files"
	@echo "  make test             Run all tests"
	@echo "  make test-hardware    Run only hardware tests"
	@echo "  make test-no-hardware Run tests without hardware"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with ruff"
	@echo "  make typecheck        Run type checking with mypy"
	@echo "  make coverage         Run tests with coverage report"
	@echo "  make pre-commit       Run pre-commit hooks"
	@echo "  make install-pre-commit Install pre-commit hooks"

# Virtual environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	@echo "Virtual environment created in $(VENV)/"
	@echo "Run 'make install-dev' to install dependencies"

# Installation targets
install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

uninstall:
	$(PIP) uninstall -y nimbie

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.orig" -delete

# Testing
test:
	$(PYTEST) -v

test-hardware:
	$(PYTEST) -v -m hardware

test-no-hardware:
	$(PYTEST) -v -m "not hardware"

# Code quality
lint:
	$(RUFF) check .

format:
	$(RUFF) format .
	$(RUFF) check --fix .

typecheck:
	$(MYPY) nimbie tests

# Coverage
coverage:
	$(PYTEST) --cov=nimbie --cov-report=html --cov-report=term-missing -v
	@echo "Coverage report generated in htmlcov/"

# Pre-commit
pre-commit:
	$(PRE_COMMIT) run --all-files

install-pre-commit:
	$(PRE_COMMIT) install

# Development workflow
check: lint typecheck test-no-hardware
	@echo "All checks passed!"

# Full check including hardware tests
check-all: lint typecheck test
	@echo "All checks passed!"