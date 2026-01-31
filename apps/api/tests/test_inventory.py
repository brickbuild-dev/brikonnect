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
async def test_inventory_crud_with_locations(db_session):
    await seed_owner(db_session, "demo", "owner@demo.local", "demo123")

    headers = {"host": "demo.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@demo.local", "password": "demo123"},
        )
        assert login.status_code == 200

        location_resp = await ac.post(
            "/api/v1/locations",
            json={"code": "A-01", "zone": "A", "aisle": "01", "shelf": "1", "bin": "1"},
        )
        assert location_resp.status_code == 201
        location_id = location_resp.json()["id"]

        create_resp = await ac.post(
            "/api/v1/inventory",
            json={
                "item_type": "PART",
                "item_no": "3001",
                "condition": "NEW",
                "qty_available": 10,
                "locations": [{"location_id": location_id, "qty": 10}],
            },
        )
        assert create_resp.status_code == 201
        item = create_resp.json()
        assert item["item_no"] == "3001"
        assert item["locations"][0]["location"]["code"] == "A-01"

        get_resp = await ac.get(f"/api/v1/inventory/{item['id']}")
        assert get_resp.status_code == 200
        item = get_resp.json()

        update_resp = await ac.patch(
            f"/api/v1/inventory/{item['id']}",
            json={"qty_available": 12, "version": item["version"]},
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["qty_available"] == 12

        conflict_resp = await ac.patch(
            f"/api/v1/inventory/{item['id']}",
            json={"qty_available": 5, "version": item["version"]},
        )
        assert conflict_resp.status_code == 409

        delete_resp = await ac.delete(f"/api/v1/inventory/{item['id']}")
        assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_inventory_bulk_and_import(db_session):
    await seed_owner(db_session, "bulk", "owner@bulk.local", "bulk123")

    headers = {"host": "bulk.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@bulk.local", "password": "bulk123"},
        )
        assert login.status_code == 200

        bulk_resp = await ac.post(
            "/api/v1/inventory/bulk",
            json={
                "items": [
                    {
                        "item_type": "PART",
                        "item_no": "3002",
                        "condition": "NEW",
                        "qty_available": 3,
                    },
                    {
                        "item_type": "PART",
                        "item_no": "3003",
                        "condition": "USED",
                        "qty_available": 4,
                    },
                ]
            },
        )
        assert bulk_resp.status_code == 200
        items = bulk_resp.json()
        assert len(items) == 2

        first = items[0]
        update_bulk = await ac.post(
            "/api/v1/inventory/bulk",
            json={
                "items": [
                    {
                        "id": first["id"],
                        "qty_available": 9,
                        "version": first["version"],
                    }
                ]
            },
        )
        assert update_bulk.status_code == 200
        assert update_bulk.json()[0]["qty_available"] == 9

        export_resp = await ac.get("/api/v1/inventory/export")
        assert export_resp.status_code == 200
        assert "text/csv" in export_resp.headers["content-type"]

        import_resp = await ac.post("/api/v1/inventory/import")
        assert import_resp.status_code == 200
        job = import_resp.json()

        job_resp = await ac.get(f"/api/v1/jobs/{job['id']}")
        assert job_resp.status_code == 200
