from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.schemas.auth import LoginIn, TokenOut
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=TokenOut)
def login_api(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    token = login(db, username=payload.username, password=payload.password, ip=request.client.host)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or inactive user")
    return {"access_token": token}
