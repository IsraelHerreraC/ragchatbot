#!/bin/bash

# Code Quality Script - Format and Check Code
# This script runs formatting and linting tools on the codebase

set -e  # Exit on error

echo "================================"
echo "Running Code Quality Checks"
echo "================================"
echo ""

# Format imports with isort
echo "[1/4] Sorting imports with isort..."
uv run isort backend --profile black
echo "✓ Import sorting complete"
echo ""

# Format code with black
echo "[2/4] Formatting code with black..."
uv run black backend
echo "✓ Code formatting complete"
echo ""

# Run flake8 linter
echo "[3/4] Running flake8 linter..."
uv run flake8 backend --count --select=E9,F63,F7,F82 --show-source --statistics
uv run flake8 backend --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
echo "✓ Linting complete"
echo ""

# Run mypy type checker
echo "[4/4] Running mypy type checker..."
uv run mypy backend --config-file=pyproject.toml || echo "⚠ Type checking found issues (non-blocking)"
echo ""

echo "================================"
echo "Code Quality Checks Complete!"
echo "================================"
