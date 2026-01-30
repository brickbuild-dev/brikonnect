from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session

async def get_session_by_token(db: AsyncSession, token: str) -> Session | None:
    q = select(Session).where(Session.session_token == token)
    return (await db.execute(q)).scalars().first()

async def delete_session(db: AsyncSession, token: str) -> None:
    await db.execute(delete(Session).where(Session.session_token == token))
