from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    expires_in,
    hash_token,
    new_refresh_token,
    new_session_token,
    utcnow,
)
from app.modules.auth.models import RefreshToken, Session
from app.modules.users.models import User


async def create_session(
    db: AsyncSession,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
) -> str:
    raw_token = new_session_token()
    token_hash = hash_token(raw_token)
    session = Session(
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=token_hash,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_in(settings.SESSION_TTL_SECONDS),
    )
    db.add(session)
    await db.flush()
    return raw_token


async def revoke_session(db: AsyncSession, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    await db.execute(delete(Session).where(Session.token_hash == token_hash))


async def get_session_by_token(db: AsyncSession, raw_token: str) -> Session | None:
    token_hash = hash_token(raw_token)
    result = await db.execute(select(Session).where(Session.token_hash == token_hash))
    return result.scalar_one_or_none()


async def create_refresh_token(
    db: AsyncSession,
    user: User,
    family_id: uuid.UUID | None = None,
) -> str:
    raw_token = new_refresh_token()
    token_hash = hash_token(raw_token)
    family = family_id or uuid.uuid4()
    refresh = RefreshToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=token_hash,
        family_id=family,
        expires_at=expires_in(settings.REFRESH_TOKEN_TTL_SECONDS),
    )
    db.add(refresh)
    await db.flush()
    return raw_token


async def get_refresh_token(db: AsyncSession, raw_token: str) -> RefreshToken | None:
    token_hash = hash_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, refresh: RefreshToken) -> None:
    refresh.revoked_at = utcnow()
    await db.flush()


async def revoke_refresh_family(db: AsyncSession, family_id: uuid.UUID) -> None:
    await db.execute(
        delete(RefreshToken).where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
    )


def build_access_token(user: User) -> str:
    return create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_TTL_SECONDS),
    )
