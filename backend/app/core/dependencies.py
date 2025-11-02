"""
Shared dependencies for FastAPI routers
"""
from sqlalchemy.orm import Session
from backend.app.core.db import SessionLocal


def get_db():
    """Get database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

