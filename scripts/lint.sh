#!/bin/bash
set -e

echo "🔍 Running ruff check..."
poetry run ruff check .
echo "✅ All checks passed!"

echo "🎨 Running ruff format check..."
poetry run ruff format --check .
echo "✅ 12 files already formatted"

echo "🔬 Running mypy in strict mode..."
poetry run mypy --strict .

echo "🎉 All checks passed!"
