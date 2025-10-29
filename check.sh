#!/bin/bash

# Code Quality Script - Check Only (No Modifications)
# This script checks code quality without making changes

set -e  # Exit on error

echo "================================"
echo "Running Code Quality Checks"
echo "(Check mode - no modifications)"
echo "================================"
echo ""

# Check import sorting
echo "[1/4] Checking import order with isort..."
uv run isort backend --profile black --check-only --diff
echo "✓ Import check complete"
echo ""

# Check code formatting
echo "[2/4] Checking code formatting with black..."
uv run black backend --check --diff
echo "✓ Format check complete"
echo ""

# Run flake8 linter
echo "[3/4] Running flake8 linter..."
uv run flake8 backend --count --select=E9,F63,F7,F82 --show-source --statistics
uv run flake8 backend --count --max-complexity=10 --max-line-length=88 --statistics
echo "✓ Linting complete"
echo ""

# Run mypy type checker
echo "[4/4] Running mypy type checker..."
uv run mypy backend --config-file=pyproject.toml || echo "⚠ Type checking found issues (non-blocking)"
echo ""

echo "================================"
echo "Code Quality Checks Complete!"
echo "================================"
