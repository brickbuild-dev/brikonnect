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
async def test_picker_flow(db_session):
    await seed_owner(db_session, "pick", "owner@pick.example.com", "pick123")

    headers = {"host": "pick.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@pick.example.com", "password": "pick123"},
        )
        assert login.status_code == 200

        location_resp = await ac.post("/api/v1/locations", json={"code": "P-01"})
        location_id = location_resp.json()["id"]

        item_resp = await ac.post(
            "/api/v1/inventory",
            json={
                "item_type": "PART",
                "item_no": "3001",
                "condition": "NEW",
                "qty_available": 5,
                "locations": [{"location_id": location_id, "qty": 5}],
            },
        )
        item_id = item_resp.json()["id"]

        order_resp = await ac.post(
            "/api/v1/orders",
            json={
                "external_order_id": "PICK-1",
                "status": "NEW",
                "lines": [
                    {
                        "item_type": "PART",
                        "item_no": "3001",
                        "condition": "NEW",
                        "qty_ordered": 2,
                        "inventory_item_id": item_id,
                    }
                ],
            },
        )
        order_id = order_resp.json()["id"]
        order_line_id = order_resp.json()["lines"][0]["id"]

        session_resp = await ac.post(
            "/api/v1/picker/sessions",
            json={"order_ids": [order_id]},
        )
        assert session_resp.status_code == 201
        session = session_resp.json()
        assert session["total_orders"] == 1
        assert session["total_items"] == 2

        route_resp = await ac.get(f"/api/v1/picker/sessions/{session['id']}/route")
        assert route_resp.status_code == 200
        assert route_resp.json()[0]["location_code"] == "P-01"

        pick_resp = await ac.post(
            f"/api/v1/picker/sessions/{session['id']}/pick",
            json={
                "order_line_id": order_line_id,
                "event_type": "PICKED",
                "qty": 2,
                "location_code": "P-01",
            },
        )
        assert pick_resp.status_code == 200

        lines_resp = await ac.get(f"/api/v1/orders/{order_id}/lines")
        assert lines_resp.status_code == 200
        assert lines_resp.json()[0]["status"] == "PICKED"
