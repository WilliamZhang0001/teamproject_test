# Backend Module - DoE-Assist

## Responsibilities
- User Authentication and Permission Management
- Business Logic Processing
- Data Processing and Validation
- Database Interaction
- Communication with Machine Learning Engine (planned)

## Tech Stack
- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- Passlib (Password Hashing)
- JWT (Authentication Tokens)
- Celery (Planned for Asynchronous Tasks)

## Project Structure
```
backend/
├── app/
│ ├── core/ # Core Config, DB Connection, Security
│ ├── models/ # SQLAlchemy ORM Models
│ ├── repos/ # Database Access Layer
│ ├── routers/ # API Routes
│ ├── schemas/ # Pydantic Schemas
│ ├── services/ # Business Logic
│ ├── main.py # FastAPI App Entrypoint
│ └── _init_.py
├── Dockerfile # Backend Service Dockerfile
├── requirements.txt # Python Dependencies
└── tests/ # Backend Tests
```

## Main API Endpoints (Sprint 1)
- `GET /health` - Health Check
- `POST /users` - Create User (Registration)
- `POST /auth/login` - User Login

## Planned API Endpoints (Sprint 2+)
- `GET /experiments` - Get Experiment List
- `POST /experiments` - Create New Experiment
- `GET /predictions` - Get Parameter Predictions
- `POST /feedback` - Submit Feedback

## Startup Commands (Local Dev)

# Install dependencies
pip install -r requirements.txt

# Run FastAPI app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Startup with Docker

# At project root
docker compose up -d --build

# Access API docs
http://localhost:8000/docs

```bash