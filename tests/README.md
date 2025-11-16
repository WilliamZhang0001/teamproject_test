# Testing Documentation - DoE-Assist

This document outlines our comprehensive testing approach, coverage, and methodology for the DoE-Assist project. This documentation serves as a guide for understanding how we ensure code quality and reliability through systematic testing.

## Table of Contents

- [Testing Approach](#testing-approach)
- [Test Structure](#test-structure)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Happy and Sad Path Testing](#happy-and-sad-path-testing)
- [Mocking and Stubbing Strategy](#mocking-and-stubbing-strategy)
- [Code Refactoring for Testability](#code-refactoring-for-testability)
- [End-to-End Testing](#end-to-end-testing)
- [Test Coverage](#test-coverage)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

## Testing Approach

Our testing strategy follows a layered approach to ensure comprehensive coverage of all code developed this term:

1. **Unit Tests**: Test individual functions and classes in isolation using mocks
2. **Integration Tests**: Test component interactions with real database and API endpoints
3. **End-to-End Tests**: Test complete user workflows (when applicable)

We follow the Single Responsibility Principle and maintain distinct layers (API, service, repository) to facilitate testing. Each layer is tested independently with appropriate mocking of dependencies.

## Test Structure

```
tests/
├── conftest.py                      # Shared pytest fixtures and configuration
├── pytest.ini                       # Pytest configuration
├── unit/                            # Unit tests (isolated, mocked dependencies)
│   ├── test_security.py             # Security function tests (password, JWT)
│   ├── test_auth_service.py         # Authentication service tests
│   ├── test_user_repo.py            # User repository tests
│   ├── test_literature_repo.py      # Literature repository tests
│   ├── test_user_experiment_repo.py # User experiment repository tests
│   └── test_experiment_service.py   # Experiment service tests
└── integration/                     # Integration tests (real database, API calls)
    ├── test_auth_router.py          # Authentication API tests
    ├── test_users_router.py         # User management API tests
    ├── test_literature_router.py    # Literature search API tests
    └── test_experiments_router.py   # Experiment prediction API tests

frontend/src/
└── components/
    └── __tests__/                   # Frontend component tests
        └── *.test.tsx
```

## Backend Testing

### Unit Tests

Unit tests focus on testing individual functions and classes in complete isolation. We use mocking extensively to isolate the code under test from external dependencies such as databases, external APIs, and other services.

#### Test Coverage Areas

1. **Security Functions** (`tests/unit/test_security.py`)
   - Password hashing and verification (happy and sad paths)
   - JWT token creation and validation
   - Token expiration handling
   - Invalid token scenarios
   - Edge cases (empty strings, special characters)

2. **Service Layer** (`tests/unit/test_auth_service.py`)
   - Business logic validation
   - Error handling for all failure scenarios
   - Mocked database interactions
   - User authentication flow
   - Inactive user handling
   - Login audit logging

3. **Repository Layer**
   - `test_user_repo.py`: User repository tests
     - Database query logic
     - Data retrieval and filtering
     - Case sensitivity handling
     - Non-existent record handling
   - `test_literature_repo.py`: Literature repository tests
     - Literature creation and retrieval
     - Similarity search algorithm
     - Parameter matching logic
     - Confidence-based queries
   - `test_user_experiment_repo.py`: User experiment repository tests
     - Experiment record creation
     - History retrieval
     - Record deletion

4. **Service Layer**
   - `test_experiment_service.py`: Experiment service tests
     - Classification prediction
     - Parameter recommendation
     - ML model integration
     - Literature integration

#### Example Unit Test with Mocking

```python
@patch('backend.app.services.auth_service.get_by_username')
@patch('backend.app.services.auth_service.verify_password')
@patch('backend.app.services.auth_service.add_login_audit')
def test_login_success(self, mock_add_audit, mock_verify_password, mock_get_user, mock_db, mock_user):
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = True
    
    result = login(mock_db, username="testuser", password="testpassword123", ip="127.0.0.1")
    
    assert result == "test_token_123"
    mock_get_user.assert_called_once_with(mock_db, "testuser")
    mock_verify_password.assert_called_once()
```

### Integration Tests

Integration tests verify that different components work together correctly. These tests use a real test database (SQLite in-memory) and test the full HTTP request/response cycle without mocking internal components.

#### Test Coverage Areas

1. **Authentication API** (`tests/integration/test_auth_router.py`)
   - HTTP request/response handling
   - Status codes and error messages
   - Successful login flow
   - Invalid credentials handling
   - Inactive user handling
   - Missing field validation

2. **User Management API** (`tests/integration/test_users_router.py`)
   - User creation (CRUD operations)
   - Data persistence
   - Duplicate username handling
   - User retrieval and updates
   - Authentication required endpoints
   - Transaction handling

3. **Literature API** (`tests/integration/test_literature_router.py`)
   - Similarity search endpoint
   - Parameter-based queries
   - Top confidence records retrieval
   - Empty result handling

4. **Experiment API** (`tests/integration/test_experiments_router.py`)
   - Classification prediction endpoint
   - Parameter recommendation endpoint
   - Experiment history retrieval
   - Record persistence
   - ML model integration

#### Example Integration Test

```python
def test_login_success(self, client, db_session, sample_user_data):
    user = AppUser(
        username=sample_user_data["username"],
        email=sample_user_data["email"],
        password_hash=hash_password(sample_user_data["password"]),
        role=sample_user_data["role"],
        is_active=sample_user_data["is_active"],
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
```

### Backend Test Requirements

Our backend tests specifically cover:

1. **Data Validation**
   - Input validation using Pydantic schemas
   - Required field validation
   - Type validation
   - Format validation (email, etc.)
   - Edge cases (empty strings, null values, special characters)

2. **Business Logic**
   - Authentication flow
   - Authorization checks
   - User state management (active/inactive)
   - Password verification
   - Token generation and validation

3. **Error Handling**
   - HTTP error codes (400, 401, 404, 422, 500)
   - Exception handling and proper error messages
   - Database error handling
   - Invalid input handling

4. **Race Conditions** (where applicable)
   - Concurrent login attempts
   - Database transaction isolation
   - Session management under concurrent load

## Frontend Testing

### Component Tests

Frontend tests use React Testing Library to test component behavior, user interactions, and rendering logic. Tests focus on what users see and interact with, rather than implementation details.

#### Test Coverage Areas

1. **Component Rendering**
   - Component renders correctly with given props
   - Conditional rendering based on state/props
   - Error boundaries and error states
   - Loading states

2. **User Interactions**
   - Form submissions
   - Button clicks and navigation
   - Input field interactions
   - Form validation feedback

3. **Integration with Context**
   - Authentication state management
   - API calls and responses
   - State updates and side effects
   - Error handling in UI

#### Example Component Test

```typescript
it('renders login form and handles submission', async () => {
  const mockLogin = jest.fn();
  render(<LoginForm onLogin={mockLogin} />);
  
  const usernameInput = screen.getByLabelText(/username/i);
  const passwordInput = screen.getByLabelText(/password/i);
  const submitButton = screen.getByRole('button', { name: /login/i });
  
  fireEvent.change(usernameInput, { target: { value: 'testuser' } });
  fireEvent.change(passwordInput, { target: { value: 'password123' } });
  fireEvent.click(submitButton);
  
  await waitFor(() => {
    expect(mockLogin).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123'
    });
  });
});
```

## Happy and Sad Path Testing

We ensure comprehensive coverage of both successful and failure scenarios:

### Happy Path Tests

Test expected successful scenarios:

- Successful login with valid credentials
- Successful user creation with valid data
- Successful data retrieval
- Successful updates and deletions
- Valid token generation and validation
- Proper password hashing and verification

### Sad Path Tests

Test error conditions and edge cases:

- Invalid credentials (wrong username/password)
- Missing required fields
- Duplicate usernames
- Non-existent resources (404 errors)
- Invalid input formats (422 errors)
- Unauthorized access (401 errors)
- Inactive user login attempts
- Expired tokens
- Malformed tokens
- Empty input fields
- Database connection failures
- Network failures (for external dependencies)

## Mocking and Stubbing Strategy

### When to Mock

We mock external dependencies to:
- Isolate the code under test
- Control test behavior and responses
- Speed up tests (avoid real database/API calls in unit tests)
- Test error conditions that are difficult to reproduce
- Ensure test independence and repeatability

### Mocking Guidelines

1. **External Services**: Always mock external APIs, third-party libraries, and services
2. **Database (Unit Tests)**: Mock database sessions and queries in unit tests
3. **Database (Integration Tests)**: Use real in-memory SQLite database
4. **Time-dependent Code**: Mock datetime for consistent test results
5. **Random Values**: Use fixed seeds or mock random functions
6. **File System**: Mock file operations when testing file handling code

### Example Mocking Patterns

#### Mocking Database in Unit Tests

```python
@patch('backend.app.services.auth_service.get_by_username')
@patch('backend.app.services.auth_service.verify_password')
def test_login_invalid_password(self, mock_verify_password, mock_get_user, mock_db, mock_user):
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = False
    
    result = login(mock_db, username="testuser", password="wrongpassword", ip="127.0.0.1")
    
    assert result is None
    mock_add_audit.assert_called_once()
```

#### Mocking External APIs

```python
@patch('requests.get')
def test_fetch_external_data(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    mock_get.return_value.status_code = 200
    
    result = fetch_external_data()
    
    assert result == {"data": "test"}
```

### Trusting External Dependencies

We do not trust the behavior of external dependencies. Therefore:
- We mock their happy and sad cases to test our code's response
- We test how our code handles external service failures
- We test timeout scenarios
- We test invalid response formats from external services

## Code Refactoring for Testability

To make our codebase more testable, we have structured it following these principles:

### Single Responsibility Principle

Each function and class has a single, well-defined responsibility:
- **Routers**: Handle HTTP requests/responses only
- **Services**: Contain business logic
- **Repositories**: Handle data access only
- **Models**: Define data structures

### Layered Architecture

We maintain distinct layers to separate concerns:

1. **API Layer** (`routers/`): HTTP request handling, validation, response formatting
2. **Service Layer** (`services/`): Business logic, orchestration
3. **Repository Layer** (`repos/`): Data access, database queries
4. **Model Layer** (`models/`): Data structures and relationships

This separation allows us to:
- Test each layer independently
- Mock dependencies easily
- Replace implementations without affecting other layers
- Write focused, maintainable tests

### Dependency Injection

We use dependency injection (via FastAPI's `Depends`) to make dependencies explicit and easily mockable:

```python
def login_api(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    # db can be easily overridden in tests
    token = login(db, username=payload.username, password=payload.password, ip=request.client.host)
```

## End-to-End Testing

### E2E Test Strategy

For end-to-end tests, we may need to call external libraries or parts of the codebase without mocking. Our E2E tests:

1. Use real database connections (test database)
2. Make actual HTTP requests to the API
3. Test complete user workflows
4. Verify data persistence across requests

### External Dependencies in E2E Tests

If E2E tests fail due to reasons outside our control (external API downtime, network issues, etc.), we document these limitations in this README:

**Known Limitations:**
- E2E tests require a running database instance
- Tests may fail if database is not properly configured
- Network-dependent tests may fail in offline environments

**Mitigation:**
- Use in-memory SQLite for most E2E tests
- Mock only truly external services (third-party APIs)
- Provide clear error messages when tests fail due to external dependencies

## Test Coverage

### Coverage Goals

- **Overall Coverage**: >80%
- **Critical Paths**: 100% (authentication, authorization, data validation)
- **Public APIs**: 100%
- **Business Logic**: >90%
- **Error Handling**: 100% of error paths

### Coverage Reports

Generate coverage reports using:

```bash
# Terminal output
pytest --cov=backend.app --cov-report=term-missing

# HTML report
pytest --cov=backend.app --cov-report=html

# XML report (for CI/CD)
pytest --cov=backend.app --cov-report=xml
```

View HTML coverage report:
```bash
# Generate and open
pytest --cov=backend.app --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Running Tests

### Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage report
pytest --cov=backend.app --cov-report=html

# Run specific test file
pytest tests/unit/test_security.py

# Run specific test class
pytest tests/unit/test_security.py::TestPasswordHashing

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests matching pattern
pytest -k "test_login"

# Run with print statements (for debugging)
pytest -s

# Run with debugger on failure
pytest --pdb
```

### Frontend Tests

```bash
# Run all tests
cd frontend
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run tests once (CI mode)
npm test -- --watchAll=false

# Run specific test file
npm test -- ComponentName.test.tsx
```

## Test Fixtures

We use pytest fixtures to provide reusable test data and setup:

### Database Fixtures

```python
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
```

### Test Client Fixture

```python
@pytest.fixture(scope="function")
def client(db_session):
    test_app = create_test_app()
    test_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()
```

### Sample Data Fixtures

```python
@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "user",
        "is_active": True
    }
```

## Test Data Management

### Data Cleanup

Each test runs in complete isolation:
- Database is created fresh for each test
- Database is dropped after each test
- No shared state between tests
- Fixtures provide clean test data

### Test Database

- **Unit Tests**: Use mocks, no database needed
- **Integration Tests**: Use SQLite in-memory database
- **E2E Tests**: Use separate test database (if needed)

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test database is properly configured in `conftest.py`
   - Check that test engine is using in-memory SQLite

2. **Import Errors**
   - Check PYTHONPATH includes project root
   - Verify relative imports are correct
   - Ensure `__init__.py` files exist in all packages

3. **Fixture Errors**
   - Verify fixture scope matches test requirements
   - Check fixture dependencies are correct
   - Ensure fixtures are properly imported

4. **Mock Errors**
   - Verify mocks are patching correct paths
   - Check mock return values match expected types
   - Ensure mocks are reset between tests

### Debugging Tests

```bash
# Run with print statements
pytest -s

# Run with debugger
pytest --pdb

# Run specific test with verbose output
pytest -vv tests/unit/test_security.py::TestPasswordHashing::test_hash_password_returns_string

# Run with coverage and show missing lines
pytest --cov=backend.app --cov-report=term-missing
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
   - Good: `test_login_fails_with_invalid_password`
   - Bad: `test_login_1`

2. **Arrange-Act-Assert**: Structure tests clearly
   ```python
   def test_example():
       # Arrange
       user = create_test_user()
       
       # Act
       result = login(user)
       
       # Assert
       assert result is not None
   ```

3. **One Assertion Per Test**: Focus each test on one behavior (when possible)

4. **Test Independence**: Tests should not depend on each other or execution order

5. **Fast Tests**: Keep tests fast for quick feedback (use mocks in unit tests)

6. **Readable Tests**: Tests should be self-documenting

7. **Maintain Tests**: Update tests when code changes

8. **Test Both Paths**: Always test both happy and sad paths

## Future Improvements

- [ ] Add E2E tests with Playwright or Cypress
- [ ] Add performance/load tests
- [ ] Add visual regression tests for frontend
- [ ] Increase coverage to 90%+
- [ ] Add mutation testing
- [ ] Add contract testing for API
- [ ] Add race condition tests for concurrent operations
- [ ] Add stress tests for database operations

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
- [Python Mocking Guide](https://docs.python.org/3/library/unittest.mock.html)
