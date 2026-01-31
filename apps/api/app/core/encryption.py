from __future__ import annotations

import base64
import hashlib
import json

from cryptography.fernet import Fernet

from app.core.config import settings


def _fernet() -> Fernet:
    raw = settings.ENCRYPTION_KEY.encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_payload(payload: dict) -> bytes:
    token = _fernet().encrypt(json.dumps(payload).encode("utf-8"))
    return token


def decrypt_payload(token: bytes) -> dict:
    raw = _fernet().decrypt(token)
    return json.loads(raw.decode("utf-8"))
