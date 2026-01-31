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
async def test_sync_preview_and_apply(db_session):
    await seed_owner(db_session, "sync", "owner@sync.example.com", "sync123")

    headers = {"host": "sync.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@sync.example.com", "password": "sync123"},
        )
        assert login.status_code == 200

        source_store = await ac.post(
            "/api/v1/stores",
            json={
                "channel": "bricklink",
                "name": "BrickLink",
                "is_primary": True,
                "settings": {
                    "mock_inventory": [
                        {
                            "external_id": "src-1",
                            "item_type": "PART",
                            "item_no": "3001",
                            "color_id": 1,
                            "condition": "NEW",
                            "qty_available": 10,
                            "unit_price": "0.50",
                        },
                        {
                            "external_id": "src-2",
                            "item_type": "PART",
                            "item_no": "3002",
                            "color_id": 1,
                            "condition": "NEW",
                            "qty_available": 5,
                            "unit_price": "0.70",
                        },
                    ]
                },
            },
        )
        assert source_store.status_code == 201

        target_store = await ac.post(
            "/api/v1/stores",
            json={
                "channel": "brickowl",
                "name": "BrickOwl",
                "is_primary": False,
                "settings": {
                    "mock_inventory": [
                        {
                            "external_id": "tgt-1",
                            "item_type": "PART",
                            "item_no": "3001",
                            "color_id": 1,
                            "condition": "NEW",
                            "qty_available": 8,
                            "unit_price": "0.50",
                        },
                        {
                            "external_id": "tgt-3",
                            "item_type": "PART",
                            "item_no": "9999",
                            "color_id": 1,
                            "condition": "NEW",
                            "qty_available": 2,
                            "unit_price": "1.00",
                        },
                    ]
                },
            },
        )
        assert target_store.status_code == 201

        preview = await ac.post(
            "/api/v1/sync/preview",
            json={
                "source_store_id": source_store.json()["id"],
                "target_store_id": target_store.json()["id"],
                "direction": "SOURCE_TO_TARGET",
                "allow_large_removals": True,
            },
        )
        assert preview.status_code == 200
        run = preview.json()["run"]
        assert run["status"] == "PREVIEW_READY"
        assert run["plan_summary"]["add"] == 1
        assert run["plan_summary"]["update"] == 1
        assert run["plan_summary"]["remove"] == 1

        plan = await ac.get(f"/api/v1/sync/runs/{run['id']}/plan")
        assert plan.status_code == 200
        assert len(plan.json()) == 3

        approve = await ac.post(f"/api/v1/sync/runs/{run['id']}/approve")
        assert approve.status_code == 200
        assert approve.json()["run"]["status"] == "COMPLETED"

        items = await ac.get("/api/v1/inventory")
        assert items.status_code == 200
        item_nos = {item["item_no"] for item in items.json()}
        assert "3001" in item_nos
        assert "3002" in item_nos
