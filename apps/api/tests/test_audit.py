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
async def test_audit_revert_inventory(db_session):
    await seed_owner(db_session, "audit", "owner@audit.example.com", "audit123")

    headers = {"host": "audit.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@audit.example.com", "password": "audit123"},
        )
        assert login.status_code == 200

        create_resp = await ac.post(
            "/api/v1/inventory/",
            json={
                "item_type": "PART",
                "item_no": "3001",
                "condition": "NEW",
                "qty_available": 5,
            },
        )
        item = create_resp.json()

        update_resp = await ac.patch(
            f"/api/v1/inventory/{item['id']}",
            json={"qty_available": 9, "version": item["version"]},
        )
        assert update_resp.status_code == 200

        audit_resp = await ac.get(
            "/api/v1/audit/",
            params={"entity_type": "inventory_item", "entity_id": item["id"]},
        )
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert logs
        latest = next(log for log in logs if log.get("before_state"))

        revert_resp = await ac.post(f"/api/v1/audit/{latest['id']}/revert")
        assert revert_resp.status_code == 200

        final_resp = await ac.get(f"/api/v1/inventory/{item['id']}")
        assert final_resp.status_code == 200
        assert final_resp.json()["qty_available"] == 5
