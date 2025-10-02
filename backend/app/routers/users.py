from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserOut
from app.models.user import AppUser

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(AppUser).filter_by(username=payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = AppUser(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
        last_login_at=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
