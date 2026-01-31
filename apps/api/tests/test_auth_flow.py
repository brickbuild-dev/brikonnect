import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import hash_password
from app.main import app
from app.modules.rbac import service as rbac_service
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, set_user_roles


@pytest.mark.asyncio
async def test_login_and_refresh(db_session):
    tenant = await create_tenant(db_session, TenantCreate(slug="demo", name="Demo"))
    await rbac_service.seed_system_roles(db_session, tenant.id)
    roles = await rbac_service.list_roles(db_session, tenant.id)
    owner_role = next(role for role in roles if role.name == "owner")

    user = await create_user(
        db_session,
        tenant.id,
        UserCreate(email="admin@demo.local", password="admin123"),
        hash_password("admin123"),
    )
    await set_user_roles(db_session, tenant.id, user.id, [owner_role.id])
    await db_session.commit()

    headers = {"host": "demo.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post("/api/v1/auth/login", json={"email": "admin@demo.local", "password": "admin123"})
        assert login.status_code == 200
        assert settings.SESSION_COOKIE_NAME in login.cookies

        me = await ac.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "admin@demo.local"

        token_resp = await ac.post("/api/v1/auth/token", json={"email": "admin@demo.local", "password": "admin123"})
        assert token_resp.status_code == 200
        payload = token_resp.json()
        assert payload["access_token"]
        assert payload["refresh_token"]

        refreshed = await ac.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": payload["refresh_token"]},
        )
        assert refreshed.status_code == 200
        refreshed_payload = refreshed.json()
        assert refreshed_payload["access_token"]
        assert refreshed_payload["refresh_token"]

        revoke = await ac.post(
            "/api/v1/auth/token/revoke",
            json={"refresh_token": refreshed_payload["refresh_token"]},
        )
        assert revoke.status_code == 200
