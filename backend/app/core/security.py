from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def new_session_token() -> str:
    return secrets.token_urlsafe(48)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def expires_in(seconds: int) -> datetime:
    return utcnow() + timedelta(seconds=seconds)

# Optional signed token (not required for cookie sessions, but handy for service-to-service)
_serializer = URLSafeTimedSerializer(settings.BRIKONNECT_SECRET_KEY, salt="brikonnect-token")

def sign_token(payload: dict) -> str:
    return _serializer.dumps(payload)

def unsign_token(token: str, max_age_seconds: int) -> dict | None:
    try:
        return _serializer.loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
