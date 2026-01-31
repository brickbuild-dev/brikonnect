from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rbac.models import Role, UserRole
from app.modules.rbac.permissions import ROLE_PERMISSIONS


async def list_roles(db: AsyncSession, tenant_id) -> list[Role]:
    result = await db.execute(select(Role).where(Role.tenant_id == tenant_id).order_by(Role.name))
    return list(result.scalars().all())


async def get_role_by_id(db: AsyncSession, tenant_id, role_id) -> Role | None:
    result = await db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.id == role_id)
    )
    return result.scalar_one_or_none()


async def create_role(db: AsyncSession, tenant_id, name: str, permissions: list[str]) -> Role:
    role = Role(tenant_id=tenant_id, name=name, permissions=permissions, is_system=False)
    db.add(role)
    await db.flush()
    return role


async def update_role(db: AsyncSession, role: Role, name: str | None, permissions: list[str] | None) -> Role:
    if name is not None:
        role.name = name
    if permissions is not None:
        role.permissions = permissions
    await db.flush()
    return role


async def delete_role(db: AsyncSession, role: Role) -> None:
    await db.execute(delete(Role).where(Role.id == role.id))


async def seed_system_roles(db: AsyncSession, tenant_id) -> list[Role]:
    roles: list[Role] = []
    for name, permissions in ROLE_PERMISSIONS.items():
        role = Role(tenant_id=tenant_id, name=name, permissions=permissions, is_system=True)
        db.add(role)
        roles.append(role)
    await db.flush()
    return roles


async def get_user_permissions(db: AsyncSession, tenant_id, user_id) -> list[str]:
    result = await db.execute(
        select(Role.permissions)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(Role.tenant_id == tenant_id, UserRole.user_id == user_id)
    )
    permissions: set[str] = set()
    for row in result.all():
        permissions.update(row[0] or [])
    return sorted(permissions)
