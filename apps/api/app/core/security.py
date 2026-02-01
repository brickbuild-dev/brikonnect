from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except ValueError:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except ValueError:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def new_session_token() -> str:
    return secrets.token_urlsafe(48)


def new_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def expires_in(seconds: int) -> datetime:
    return utcnow() + timedelta(seconds=seconds)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_access_token(subject: str, tenant_id: str, expires_delta: timedelta) -> str:
    now = utcnow()
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
