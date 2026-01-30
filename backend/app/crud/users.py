from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

async def get_user_by_email(db: AsyncSession, tenant_id: int, email: str) -> User | None:
    q = select(User).where(User.tenant_id == tenant_id, User.email == email)
    return (await db.execute(q)).scalars().first()

async def create_user(db: AsyncSession, tenant_id: int, email: str, password_hash: str, is_superuser: bool = False) -> User:
    user = User(tenant_id=tenant_id, email=email, password_hash=password_hash, is_superuser=is_superuser)
    db.add(user)
    await db.flush()
    return user
