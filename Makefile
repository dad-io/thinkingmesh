.PHONY: help install install-dev test test-cov lint format check clean build docs

help:
	@echo "ThinkingMesh Development Commands"
	@echo "================================="
	@echo "install        Install package in development mode"
	@echo "install-dev    Install package with development dependencies"
	@echo "test           Run tests"
	@echo "test-cov       Run tests with coverage"
	@echo "lint           Run linting (ruff + mypy)"
	@echo "format         Format code (black + ruff)"
	@echo "check          Run all quality checks"
	@echo "clean          Clean build artifacts"
	@echo "build          Build package"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/

test-cov:
	pytest tests/ --cov=thinkingmesh --cov-report=html --cov-report=term

lint:
	ruff check thinkingmesh tests
	mypy thinkingmesh

format:
	black thinkingmesh tests
	ruff check --fix thinkingmesh tests

check: lint test

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docs:
	@echo "Documentation generation not yet implemented"