# Tests Module - DoE-Assist

## Responsibilities
- Unit Testing
- Integration Testing
- End-to-End Testing
- Performance Testing
- Test Data Management

## Tech Stack
- pytest
- pytest-asyncio
- pytest-cov
- selenium (E2E testing)
- locust (Performance testing)

## Project Structure
```
tests/
├── unit/             # Unit Tests
├── integration/      # Integration Tests
├── e2e/             # End-to-End Tests
├── fixtures/        # Test Fixtures
└── data/            # Test Data
```

## Test Types
1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test module interactions
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Test system performance under load

## Running Tests
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_experiments.py
```

## Test Coverage
- Target: >80% code coverage
- Critical paths: 100% coverage
- All public APIs must be tested

## Test Data
- Use fixtures for consistent test data
- Separate test databases
- Mock external services
