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
async def test_locations_crud(db_session):
    await seed_owner(db_session, "loc", "owner@loc.example.com", "loc123")

    headers = {"host": "loc.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@loc.example.com", "password": "loc123"},
        )
        assert login.status_code == 200

        create_resp = await ac.post(
            "/api/v1/locations/",
            json={"code": "B-01", "zone": "B", "aisle": "01"},
        )
        assert create_resp.status_code == 201
        location = create_resp.json()

        update_resp = await ac.patch(
            f"/api/v1/locations/{location['id']}",
            json={"shelf": "2", "bin": "3"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["shelf"] == "2"

        delete_resp = await ac.delete(f"/api/v1/locations/{location['id']}")
        assert delete_resp.status_code == 204
