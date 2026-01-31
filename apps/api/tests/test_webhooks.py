import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.main import app
from app.modules.rbac import service as rbac_service
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, set_user_roles


async def seed_owner(db_session, slug: str, email: str, password: str):
    tenant = await create_tenant(db_session, TenantCreate(slug=slug, name=slug.title()))
    await rbac_service.seed_system_roles(db_session, tenant.id)
    roles = await rbac_service.list_roles(db_session, tenant.id)
    owner_role = next(role for role in roles if role.name == "owner")
    user = await create_user(
        db_session,
        tenant.id,
        UserCreate(email=email, password=password),
        hash_password(password),
    )
    await set_user_roles(db_session, tenant.id, user.id, [owner_role.id])
    await db_session.commit()
    return tenant, user


@pytest.mark.asyncio
async def test_webhooks_crud(db_session):
    await seed_owner(db_session, "hooks", "owner@hooks.local", "hooks123")

    headers = {"host": "hooks.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@hooks.local", "password": "hooks123"},
        )
        assert login.status_code == 200

        create_resp = await ac.post(
            "/api/v1/webhooks",
            json={"url": "https://example.com/hook", "events": ["order.created"]},
        )
        assert create_resp.status_code == 201
        webhook = create_resp.json()

        list_resp = await ac.get("/api/v1/webhooks")
        assert list_resp.status_code == 200
        assert list_resp.json()

        update_resp = await ac.patch(
            f"/api/v1/webhooks/{webhook['id']}",
            json={"is_enabled": False},
        )
        assert update_resp.status_code == 200

        test_resp = await ac.post(f"/api/v1/webhooks/{webhook['id']}/test")
        assert test_resp.status_code == 200

        delete_resp = await ac.delete(f"/api/v1/webhooks/{webhook['id']}")
        assert delete_resp.status_code == 204
