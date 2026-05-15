.PHONY: help install install-dev test test-cov lint format format-check clean docs docs-clean build upload-test upload all-checks

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install the package with development dependencies
	pip install -e ".[dev,docs]"
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage report
	pytest --cov=reporthanter --cov-report=html --cov-report=term

lint:  ## Run linting (ruff check + mypy)
	ruff check reporthanter tests
	mypy reporthanter

format:  ## Format code (ruff)
	ruff check --fix reporthanter tests
	ruff format reporthanter tests

format-check:  ## Check code formatting without changing files
	ruff check reporthanter tests
	ruff format --check reporthanter tests

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:  ## Build documentation
	cd docs && make html

docs-clean:  ## Clean documentation build
	cd docs && make clean

build:  ## Build package
	python -m build

upload-test:  ## Upload to TestPyPI
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:  ## Upload to PyPI
	twine upload dist/*

all-checks:  ## Run all checks (format-check, lint, test)
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test
