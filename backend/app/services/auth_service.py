from datetime import datetime
from sqlalchemy.orm import Session
from app.repos.user_repo import get_by_username
from app.repos.auth_repo import add_login_audit
from app.core.security import verify_password, create_access_token

def login(db: Session, *, username: str, password: str, ip: str | None):
    user = get_by_username(db, username)
    ok = bool(user and user.is_active and verify_password(password, user.password_hash))

    add_login_audit(db, user_id=(user.id if user else None), username=username, ip=ip, ok=ok)
    db.commit()

    if not ok:
        return None

    # update last_login_at
    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_access_token(sub=str(user.id))
    return token
