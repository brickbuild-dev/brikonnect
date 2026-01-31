from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.rbac import service as rbac_service
from app.modules.tenants import service as tenant_service
from app.modules.tenants.schemas import TenantCreate
from app.modules.users import service as user_service
from app.modules.users.schemas import UserCreate


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        await _seed_data(db)
        await db.commit()


async def _seed_data(db: AsyncSession) -> None:
    tenant = await tenant_service.get_tenant_by_slug(db, "demo")
    if not tenant:
        tenant = await tenant_service.create_tenant(
            db,
            TenantCreate(slug="demo", name="Demo Tenant"),
        )

    existing_roles = await rbac_service.list_roles(db, tenant.id)
    if not existing_roles:
        await rbac_service.seed_system_roles(db, tenant.id)

    user = await user_service.get_user_by_email(db, tenant.id, "admin@demo.local")
    if not user:
        user = await user_service.create_user(
            db,
            tenant.id,
            UserCreate(
                email="admin@demo.local",
                password="admin123",
                display_name="Demo Admin",
                is_active=True,
            ),
            hash_password("admin123"),
        )

    owner_role = next(
        (role for role in await rbac_service.list_roles(db, tenant.id) if role.name == "owner"),
        None,
    )
    if owner_role:
        await user_service.set_user_roles(db, tenant.id, user.id, [owner_role.id])


if __name__ == "__main__":
    asyncio.run(seed())
