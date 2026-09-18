from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import uuid
import bcrypt
import jwt
from fastapi import HTTPException, status
from .config import settings
from ..services.session_service import session_service

logger = logging.getLogger("security")

def _unauthorized(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    # jti makes every token unique, even two logins in the same second
    encoded_jwt = jwt.encode({**data, "exp": expire, "jti": uuid.uuid4().hex}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    session_service.create_session(data["sub"], encoded_jwt, expire)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except ValueError:
        # bcrypt rejects passwords over 72 bytes and malformed hashes
        return False

def get_password_hash(password: str) -> str:
    # Raises ValueError over 72 bytes; UserCreate caps the length before we get here
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise _unauthorized()
    try:
        revoked = session_service.is_token_blacklisted(token)
    except Exception as e:
        # Fail closed: without the revocation list we can't trust any token
        logger.error(f"Token revocation check failed: {e}")
        raise _unauthorized()
    if revoked:
        raise _unauthorized("Token has been invalidated")
    return payload
