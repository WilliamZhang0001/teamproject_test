# Database Module - DoE-Assist

## Responsibilities
- Database Schema Design (Users, Audit, Experiments, Parameters, etc.)
- Data Migration Management (Alembic planned)
- Data Validation and Constraints
- Query Optimization and Index Management

## Tech Stack
- MySQL 8.0 (Primary Database, Dockerized)
- SQLAlchemy (ORM)
- Alembic (Migration Management, to be integrated later)

## Current Database Design

### Core Tables (Sprint 1)
1. **app_user** - User Accounts
   - `id`, `username`, `email`, `password_hash`, `role`, `is_active`, `created_at`, `last_login_at`
   - `username` unique
2. **auth_login_audit** - Login Attempts
   - `id`, `user_id`, `username`, `ip`, `ok`, `created_at`
   - Foreign key → `app_user.id`

### Planned Extensions (Sprint 2+)
- **experiments** - Experiment Records
- **parameters** - Experimental Parameters
- **results** - Experimental Results
- **literature_data** - Literature Data
- **predictions** - Prediction Results
- **feedback** - User Feedback

### Relationship Design (Planned)
- User ↔ Experiment (One-to-Many)
- Experiment ↔ Parameter (One-to-Many)
- Experiment ↔ Result (One-to-Many)
- Parameter ↔ Prediction (Many-to-Many)

## Project Structure
```
database/
├── db/init/ # Initialization SQL scripts (001_users.sql etc.)
├── models/ # SQLAlchemy ORM models
├── migrations/ # Alembic migration files (planned)
├── seeds/ # Seed Data (planned)
└── scripts/ # Utility scripts (planned)
```

## Data Model Features
- Current:
  - User authentication & audit logging
  - Secure password hashing (bcrypt / pbkdf2)
- Planned:
  - Support for multiple experiment types
  - Flexible parameter storage
  - Version control and auditing
  - Data integrity constraints across entities

## Usage Example
```python
from app.models.user import AppUser
from app.models.auth import AuthLoginAudit
from datetime import datetime

# Create new user
user = AppUser(
    username="alice",
    email="alice@example.com",
    password_hash="<hashed_password>",
    role="user",
    is_active=True,
    created_at=datetime.utcnow()
)

# Record login attempt
audit = AuthLoginAudit(
    user_id=user.id,
    username=user.username,
    ip="127.0.0.1",
    ok=True,
    created_at=datetime.utcnow()
)
