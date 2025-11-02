from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, Header
from sqlalchemy.orm import Session
from backend.app.core.dependencies import get_db
from backend.app.core.security import hash_password, verify_token
from backend.app.schemas.user import UserCreate, UserOut, UserUpdate
from backend.app.models.user import AppUser

router = APIRouter(prefix="/users", tags=["users"])


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

@router.get("/me", response_model=UserOut)
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Get current user information"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.split(" ")[1]
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.get(AppUser, int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserOut.model_validate(user)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.username and payload.username != user.username:
        exists = db.query(AppUser).filter_by(username=payload.username).first()
        if exists:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = payload.username

    if payload.email is not None:
        user.email = payload.email

    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    if payload.role is not None:
        user.role = payload.role

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.last_login_at is not None:
        user.last_login_at = payload.last_login_at

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return Response(status_code=204)