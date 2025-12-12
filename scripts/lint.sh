#!/bin/bash
set -e

echo "Running ruff check..."
poetry run ruff check .

echo "Running ruff format check..."
poetry run ruff format --check .

echo "Running mypy in strict mode..."
poetry run mypy --strict .

echo "All checks passed!"
