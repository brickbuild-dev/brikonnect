import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.main import app
from app.modules.rbac import service as rbac_service
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, set_user_roles


@pytest.mark.asyncio
async def test_tenant_isolation(db_session):
    tenant_a = await create_tenant(db_session, TenantCreate(slug="alpha", name="Alpha"))
    tenant_b = await create_tenant(db_session, TenantCreate(slug="beta", name="Beta"))

    await rbac_service.seed_system_roles(db_session, tenant_a.id)
    await rbac_service.seed_system_roles(db_session, tenant_b.id)

    role_a = next(role for role in await rbac_service.list_roles(db_session, tenant_a.id) if role.name == "owner")
    role_b = next(role for role in await rbac_service.list_roles(db_session, tenant_b.id) if role.name == "owner")

    user_a = await create_user(
        db_session,
        tenant_a.id,
        UserCreate(email="owner@alpha.example.com", password="alpha123"),
        hash_password("alpha123"),
    )
    user_b = await create_user(
        db_session,
        tenant_b.id,
        UserCreate(email="owner@beta.example.com", password="beta123"),
        hash_password("beta123"),
    )
    await set_user_roles(db_session, tenant_a.id, user_a.id, [role_a.id])
    await set_user_roles(db_session, tenant_b.id, user_b.id, [role_b.id])
    await db_session.commit()

    headers = {"host": "alpha.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@alpha.example.com", "password": "alpha123"},
        )
        assert login.status_code == 200

        users = await ac.get("/api/v1/users/")
        assert users.status_code == 200
        emails = {u["email"] for u in users.json()}
        assert "owner@alpha.example.com" in emails
        assert "owner@beta.example.com" not in emails
