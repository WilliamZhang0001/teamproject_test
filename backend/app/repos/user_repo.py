from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import AppUser

def get_by_username(db: Session, username: str) -> AppUser | None:
    return db.scalar(select(AppUser).where(AppUser.username == username))
