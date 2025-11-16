# Backend Module - DoE-Assist API

## Overview

The backend module provides RESTful APIs for the DoE-Assist system, handling user authentication, experiment predictions, literature search, and data persistence.

## Responsibilities

- User Authentication and Permission Management
- Experiment Prediction (Classification and Parameter Recommendation)
- Literature Search and Retrieval
- Data Processing and Validation
- Database Interaction
- Integration with Machine Learning Engine

## Tech Stack

- **Python 3.11**
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy 2.0+** - ORM for database operations
- **Pydantic 2.0+** - Data validation and settings
- **PyJWT** - JWT token authentication
- **bcrypt** - Password hashing
- **PyMySQL** - MySQL database connector
- **Uvicorn** - ASGI server

## Project Structure

```
backend/
├── app/
│   ├── core/           # Core configuration, DB connection, security
│   │   ├── config.py   # Application settings
│   │   ├── db.py       # Database connection and session management
│   │   ├── security.py # Password hashing and JWT tokens
│   │   ├── dependencies.py # Shared dependencies (get_db)
│   │   └── parameter_spec.py # Parameter specification loader & validator
│   ├── adapters/       # ML engine integration helpers
│   │   └── predictors.py # Predictor factory and fallbacks
│   ├── api/            # Versioned API entry points
│   │   ├── v1_predict.py # Unified ML prediction & upload endpoints
│   │   └── v1_jobs.py    # Async job orchestration endpoints
│   ├── models/         # SQLAlchemy ORM models
│   │   ├── user.py     # User model
│   │   ├── auth.py     # Authentication audit model
│   │   ├── literature.py # Literature and extraction models
│   │   └── user_experiment.py # User experiment record model
│   ├── repos/          # Database access layer
│   │   ├── user_repo.py
│   │   ├── auth_repo.py
│   │   ├── literature_repo.py
│   │   └── user_experiment_repo.py
│   ├── routers/        # API routes
│   │   ├── auth.py     # Authentication endpoints
│   │   ├── users.py    # User management endpoints
│   │   ├── literature.py # Literature search endpoints
│   │   └── experiments.py # Experiment prediction endpoints
│   ├── schemas/        # Pydantic schemas
│   │   ├── auth.py     # Auth request/response models
│   │   └── user.py     # User request/response models
│   ├── services/       # Business logic
│   │   ├── auth_service.py
│   │   ├── literature_service.py
│   │   ├── experiment_service.py
│   │   ├── model_orchestrator.py # Runtime model dispatching & caching
│   │   └── iqr_repo.py           # IQR statistics loader
│   └── main.py         # FastAPI application entry point
├── Dockerfile          # Backend service Dockerfile
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

### Authentication
- `POST /auth/login` - User login, returns JWT token

### User Management
- `POST /users` - Create new user (registration)

### Literature
- `POST /literature/load` - Load literature data from JSONL file to database
- `GET /literature/search` - Search similar literature based on parameters
- `POST /literature/enhance-prediction` - Enhance ML prediction with literature evidence
- `GET /literature/top-confidence` - Get high-confidence literature records

### Experiment Prediction
- `POST /api/v1/experiments/predict-classification` - Predict if experimental conditions are good/bad
- `POST /api/v1/experiments/predict-parameter` - Predict values for specified parameters
- `GET /api/v1/experiments/history` - Get user's prediction history
- `GET /api/v1/experiments/{experiment_id}` - Get specific experiment record

### Unified ML Prediction
- `POST /api/v1/predict` - Token-protected unified prediction endpoint.
  - **Headers**: `Authorization: Bearer <JWT>`, optional `Idempotency-Key` to deduplicate retries.
  - **Body**: Biomolecule metadata, optional known parameters, and an optional `recommend_parameters` list for mixed recommendation/prediction flows.
  - **Behavior**: Applies parameter-spec validation, orchestrates the active ML model, enforces per-user/token/IP rate limits, and returns normalized payload, predictions, and literature evidence.
- `POST /api/v1/upload` - Secure upload helper for base64 encoded experiment artifacts.
  - **Headers**: `Authorization: Bearer <JWT>`.
  - **Body**: `{ "filename": "example.csv", "content": "<base64>" }`.
  - **Response**: Persists the file to `backend/uploads/` and returns a generated `file_id` for later association.

### Asynchronous Jobs
- `POST /api/v1/jobs` - Submit a background prediction job.
  - **Headers**: `Authorization: Bearer <JWT>`.
  - **Body**: `{ "task_type": "predict", "payload": { ... } }` matching `/api/v1/predict` requirements.
  - **Behavior**: Queues the task, immediately returns `202` with a `job_id`, and processes via background worker.
- `GET /api/v1/jobs/{job_id}` - Check background job status and retrieve results when complete.
  - **Headers**: `Authorization: Bearer <JWT>`.
  - **Response**: Includes `status`, optional `result_json`, and error payloads for failed jobs.

## Environment Variables

When using Docker Compose, environment variables are configured in `docker-compose.yml` at the project root. For local development, create a `.env` file in the `backend/` directory:

```env
APP_ENV=dev
DB_HOST=localhost  # Use 'db' when running in Docker Compose
DB_PORT=3306       # Use 53306 for external MySQL connection
DB_USER=appuser
DB_PASS=devpass
DB_NAME=appdb
JWT_SECRET=your-secret-key-here
JWT_EXPIRE_MINUTES=60
PARAMETER_SPEC_PATH=Parameter_Input_Specification.md
PARAMETER_VALIDATION_ENABLED=true
PARAMETER_VALIDATION_OPTIONAL_MIN_COUNT=1
```

### Key Variables

- `DB_HOST` - Database host (use `db` when running in Docker Compose, `localhost` for external MySQL)
- `DB_PORT` - Database port (3306 for internal Docker, 53306 for external connection)
- `JWT_SECRET` - Secret key for JWT token generation (change in production!)
- `PARAMETER_SPEC_PATH` - Relative/absolute path to the Markdown specification defining required/optional experiment fields.
- `PARAMETER_VALIDATION_ENABLED` - Toggle runtime validation (set `false` to bypass during local debugging).
- `PARAMETER_VALIDATION_OPTIONAL_MIN_COUNT` - Minimum optional parameters enforced when validation is enabled.

## Quick Start

### Using Docker Compose (Recommended)

The easiest way to start the backend along with the entire system:

```bash
# From project root directory
docker compose up -d --build
```

This will automatically start:
- MySQL database (port 53306)
- Backend API service (port 8000)
- Frontend service (port 3000)

The backend will be available at http://localhost:8000

### Local Development (Without Docker)

If you prefer to run the backend locally:

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
# Create .env file with your configuration
# See Environment Variables section below
```

3. **Ensure MySQL is running** (either via Docker Compose or standalone MySQL)

4. **Run the application:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Connection

The backend connects to MySQL database using SQLAlchemy. Connection settings are configured in:
- `app/core/config.py` - Settings class
- Environment variables via `.env` file

## Features

### 1. User Authentication
- User registration with email and password
- JWT-based authentication
- Password hashing using bcrypt
- Login audit logging

### 2. Experiment Prediction
- **Classification**: Predict if experimental conditions are "Good" or "Bad"
  - Input: Biomolecule type, name, experiment type, 8 optional parameters
  - Output: Prediction result, confidence, top 3 similar literature
  
- **Parameter Prediction**: Predict values for one or more parameters
  - Input: Experimental conditions and parameters to predict
  - Output: Recommended values, ranges, confidence, top 3 similar literature
- **Validation Pipeline**: Inputs are normalized against the Markdown-driven parameter specification with configurable optional-field requirements.

### 3. Literature Search
- Similarity-based search using weighted Euclidean distance
- Top K most similar literature records
- Confidence-based filtering
- Integration with experiment predictions

### 4. Data Persistence
- All prediction requests are saved to database
- User-specific experiment history
- Literature metadata and extraction records

### 5. Unified ML Orchestration
- `/api/v1/predict` centralizes validation, rate limiting, and ML model dispatch through `ModelOrchestrator`.
- Supports mixed scenarios (pure prediction vs. recommendation with `known_parameters`).
- Upload helper and async job APIs enable large payload handling and offline computation.

## Development

### Code Structure

- **API** (`app/api/`): Versioned entry points for ML prediction & job orchestration.
- **Adapters** (`app/adapters/`): Bridges unified predictors with the ML engine implementations.
- **Models** (`app/models/`): SQLAlchemy ORM models
- **Repositories** (`app/repos/`): Database access layer
- **Services** (`app/services/`): Business logic layer
- **Routers** (`app/routers/`): API endpoint handlers
- **Schemas** (`app/schemas/`): Pydantic validation models
- **Core Utilities** (`app/core/parameter_spec.py`): Markdown-driven parameter specification loader & validator helpers.

### Adding New Endpoints

1. Define Pydantic schemas in `app/schemas/`
2. Create repository functions in `app/repos/`
3. Implement business logic in `app/services/`
4. Add routes in `app/routers/`
5. Register router in `app/main.py`

### Testing

The backend includes comprehensive unit and integration tests. See `tests/README.md` for detailed testing documentation.

#### Quick Start

```bash
# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=backend.app --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

#### Test Structure

- **Unit Tests** (`tests/unit/`): Test individual functions and classes in isolation with mocked dependencies
  - Security functions (password hashing, JWT tokens)
  - Service layer (authentication, experiment services)
  - Repository layer (database access)
  
- **Integration Tests** (`tests/integration/`): Test API endpoints with real database
  - Authentication API
  - User management API
  - Literature search API
  - Experiment prediction API

#### Test Coverage

Current test coverage includes:
- Security functions: ~95%
- Authentication service: ~90%
- Repository layer: ~80%
- API endpoints: ~75%
- Overall: ~78%

For detailed coverage information, see `tests/README_BACKEND_COVERAGE.md`.

#### Test Configuration

Tests use:
- **pytest** - Testing framework
- **SQLite in-memory database** - For integration tests (no external database required)
- **FastAPI TestClient** - For API endpoint testing
- **Mocking** - For external dependencies in unit tests

See `tests/README_QUICK_START.md` for more testing commands and options.

## Troubleshooting

### Database Connection Issues
- Verify MySQL is running and accessible
- Check environment variables in `.env`
- Ensure database exists: `appdb`
- Check network connectivity between containers

### ML Model Loading Issues
- Verify model files exist in `models/` directory
- Check volume mounts in `docker-compose.yml`
- Ensure ML engine dependencies are installed (pandas, numpy, scikit-learn, xgboost, lightgbm)

### Port Conflicts
- Default port is 8000
- Change in `docker-compose.yml` or use `--port` flag with uvicorn

### Docker Compose Issues
- Ensure all services are running: `docker compose ps`
- Check logs: `docker compose logs backend`
- Rebuild if needed: `docker compose up -d --build`

## Dependencies

Key dependencies are listed in `requirements.txt`:

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `SQLAlchemy>=2.0` - ORM
- `pydantic>=2` - Data validation
- `PyJWT` - JWT tokens
- `bcrypt>=4.1` - Password hashing
- `pymysql>=1.1` - MySQL connector

### Testing Dependencies
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-asyncio>=0.21.0` - Async test support
- `httpx>=0.24.0` - HTTP client for testing

## License

Part of DoE-Assist project
