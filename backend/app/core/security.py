from datetime import datetime, timedelta,timezone
import jwt
import bcrypt
from backend.app.core.config import settings

def hash_password(raw: str) -> str:
    # Use bcrypt directly to avoid passlib compatibility issues
    salt = bcrypt.gensalt()
    password_bytes = raw.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(raw: str, hashed: str) -> bool:
    # Use bcrypt directly to avoid passlib compatibility issues
    password_bytes = raw.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": sub, "exp": expire}, settings.jwt_secret, algorithm="HS256")

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.JWTError:
        raise Exception("Invalid token")
