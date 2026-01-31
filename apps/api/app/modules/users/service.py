from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rbac.models import Role, UserRole
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate


async def get_user_by_id(db: AsyncSession, tenant_id, user_id) -> User | None:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, tenant_id, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == email)
    )
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession, tenant_id) -> list[User]:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
    )
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    tenant_id,
    payload: UserCreate,
    password_hash: str,
) -> User:
    user = User(
        tenant_id=tenant_id,
        email=payload.email,
        password_hash=password_hash,
        display_name=payload.display_name,
        is_active=payload.is_active,
    )
    db.add(user)
    await db.flush()
    return user


async def update_user(db: AsyncSession, user: User, payload: UserUpdate) -> User:
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.password_hash = payload.password
    await db.flush()
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.execute(delete(User).where(User.id == user.id))


async def set_user_roles(
    db: AsyncSession, tenant_id, user_id, role_ids: list
) -> list[Role]:
    if not role_ids:
        return []
    result = await db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.id.in_(role_ids))
    )
    roles = list(result.scalars().all())

    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    for role in roles:
        db.add(UserRole(user_id=user_id, role_id=role.id))
    await db.flush()
    return roles
