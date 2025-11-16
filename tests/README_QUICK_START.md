# Quick Start Guide for Running Tests

## Prerequisites

1. Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

## Running Tests

### Run All Tests
```bash
# From project root
pytest

# Or from backend directory
cd backend
pytest ../tests
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_security.py

# Run specific test class
pytest tests/unit/test_security.py::TestPasswordHashing

# Run specific test function
pytest tests/unit/test_security.py::TestPasswordHashing::test_hash_password_returns_string
```

### Run with Coverage

```bash
# Terminal output
pytest --cov=backend.app --cov-report=term-missing

# HTML report
pytest --cov=backend.app --cov-report=html
# Then open htmlcov/index.html in browser

# XML report (for CI/CD)
pytest --cov=backend.app --cov-report=xml
```

### Run with Verbose Output

```bash
# Verbose output
pytest -v

# Very verbose
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

### Run Tests Matching Pattern

```bash
# Run tests matching "login"
pytest -k "login"

# Run tests matching "auth" or "user"
pytest -k "auth or user"

# Exclude tests matching "slow"
pytest -k "not slow"
```

### Run with Markers

```bash
# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit

# Run auth-related tests
pytest -m auth
```

## Common Issues

### Import Errors

If you get import errors, ensure you're running from the project root:
```bash
# From project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database Connection Errors

Tests use in-memory SQLite, so no database setup is needed. If you see connection errors, check that `conftest.py` is properly configured.

### Fixture Errors

Ensure all fixtures are properly defined in `conftest.py`. If a fixture is missing, add it to `conftest.py`.

## Test Structure

- `tests/conftest.py`: Shared fixtures and configuration
- `tests/pytest.ini`: Pytest configuration
- `tests/unit/`: Unit tests (mocked dependencies)
- `tests/integration/`: Integration tests (real database)

## Expected Test Count

- Unit Tests: ~50 tests
- Integration Tests: ~35 tests
- Total: ~85 tests

## Test Execution Time

- Unit tests: ~5-10 seconds
- Integration tests: ~10-15 seconds
- Total: ~15-25 seconds

