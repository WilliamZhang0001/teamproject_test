from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.dependencies import get_db
from backend.app.schemas.auth import LoginIn, TokenOut
from backend.app.schemas.user import UserOut
from backend.app.services.auth_service import login
from backend.app.repos.user_repo import get_by_username

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login_api(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    token = login(db, username=payload.username, password=payload.password, ip=request.client.host)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Get user info
    user = get_by_username(db, payload.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        }
    }
