from sqlalchemy.orm import Session
from datetime import datetime
from app.models.auth import AuthLoginAudit

def add_login_audit(db: Session, *, user_id: int | None, username: str | None, ip: str | None, ok: bool):
    db.add(AuthLoginAudit(
        user_id=user_id, username=username, ip=ip, ok=ok, created_at=datetime.utcnow()
    ))