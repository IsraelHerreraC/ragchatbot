# Code Quality Tools

This project uses automated code quality tools to maintain consistent code style and catch potential issues early in development.

## Tools Overview

### Black - Code Formatter
- **Purpose**: Enforces consistent code formatting across the entire codebase
- **Configuration**: `pyproject.toml` [tool.black] section
- **Line Length**: 88 characters (PEP 8 compliant)
- **Target**: Python 3.13

### isort - Import Organizer
- **Purpose**: Automatically sorts and organizes import statements
- **Configuration**: `pyproject.toml` [tool.isort] section
- **Profile**: Black-compatible (ensures no conflicts with black)
- **Order**: Standard library → Third-party → Local imports

### Flake8 - Linter
- **Purpose**: Checks code for style violations and potential bugs
- **Configuration**: `.flake8` file
- **Max Line Length**: 88 characters
- **Max Complexity**: 10 (cyclomatic complexity)
- **Ignored**: E203, E266, E501, W503 (black-compatible ignores)

### Mypy - Type Checker
- **Purpose**: Static type checking to catch type-related errors
- **Configuration**: `pyproject.toml` [tool.mypy] section
- **Mode**: Gradual typing (non-strict, imports ignored)
- **Excludes**: tests, chroma_db, .venv

## Quick Start

### Format Your Code (Recommended before commit)

**Windows:**
```bash
format.bat
```

**Linux/Mac:**
```bash
./format.sh
```

This will:
1. Sort all imports with isort
2. Format code with black
3. Check for linting issues with flake8
4. Run type checking with mypy

### Check Code Quality (No Modifications)

**Windows:**
```bash
check.bat
```

**Linux/Mac:**
```bash
./check.sh
```

This runs all checks without modifying any files, useful for CI/CD or pre-push validation.

## Individual Tool Usage

```bash
# Format with black
uv run black backend

# Check formatting without changes
uv run black backend --check

# Sort imports
uv run isort backend --profile black

# Check import order without changes
uv run isort backend --check-only

# Run linter
uv run flake8 backend

# Run type checker
uv run mypy backend
```

## Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest backend/tests/test_ai_generator.py

# Run with verbose output
uv run pytest -v

# Generate coverage report
uv run pytest --cov=backend --cov-report=html
```

## Configuration Files

- **pyproject.toml** - Main configuration for black, isort, mypy, and pytest
- **.flake8** - Flake8-specific configuration
- **format.sh / format.bat** - Convenience scripts for running all formatters
- **check.sh / check.bat** - Convenience scripts for checking code quality

## Best Practices

1. **Before Committing**: Always run `format.sh` or `format.bat` to ensure code is properly formatted
2. **During Development**: Configure your IDE to run black and isort on save
3. **Review Changes**: After formatting, review the changes to ensure they make sense
4. **Type Hints**: Gradually add type hints to improve mypy coverage
5. **Flake8 Warnings**: Address flake8 warnings when reasonable, but focus on errors first

## CI/CD Integration

For continuous integration, use the check scripts:

```yaml
# Example GitHub Actions snippet
- name: Check code quality
  run: |
    chmod +x check.sh
    ./check.sh
```

## Troubleshooting

### Black and Flake8 Conflicts
The configuration is set to avoid conflicts between black and flake8. If you encounter issues:
- Check `.flake8` has the correct ignore list: E203, E266, E501, W503
- Ensure line length matches in both configs (88)

### Import Sorting Issues
If isort and black conflict:
- Verify isort profile is set to "black" in `pyproject.toml`
- Run isort before black: `uv run isort backend && uv run black backend`

### Mypy Errors
Mypy is configured for gradual typing (non-strict):
- Focus on critical errors first
- Add `# type: ignore` comments sparingly for third-party library issues
- Gradually improve type coverage over time

## Adding New Dependencies

When adding quality tools as dependencies:

```bash
# Add development dependency
uv add --dev package-name

# Remove dependency
uv remove package-name

# Sync all dependencies
uv sync
```

## Editor Integration

### VS Code
Install extensions:
- Python (Microsoft)
- Black Formatter
- isort
- Flake8
- Mypy

Add to `.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm
1. Go to Settings → Tools → Black
2. Enable "Run black on save"
3. Go to Settings → Tools → isort
4. Enable "Run isort on save"
5. Enable Flake8 and Mypy inspections

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
