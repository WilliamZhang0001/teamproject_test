from datetime import datetime, timedelta, timezone
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
    """Create JWT access token
    
    If jwt_expire_minutes is None, token never expires (permanent until logout).
    Otherwise, token expires after specified minutes.
    """
    payload = {"sub": sub}
    
    # Only add expiration if configured
    if settings.jwt_expire_minutes is not None:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        payload["exp"] = expire
    
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload
    
    If token has no expiration (exp claim), it will never expire.
    Only invalid tokens will raise exceptions.
    """
    try:
        # Use options to not require expiration check
        # If exp is present, it will be validated; if not, token is permanent
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=["HS256"],
            options={"verify_exp": True}  # Verify exp only if present
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Invalid token: {str(e)}")
