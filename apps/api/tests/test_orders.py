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
async def test_orders_status_flow(db_session):
    await seed_owner(db_session, "orders", "owner@orders.local", "orders123")

    headers = {"host": "orders.brikonnect.com"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as ac:
        login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "owner@orders.local", "password": "orders123"},
        )
        assert login.status_code == 200

        create_resp = await ac.post(
            "/api/v1/orders",
            json={
                "external_order_id": "BL-1001",
                "status": "NEW",
                "buyer_name": "Brick Buyer",
                "lines": [
                    {
                        "item_type": "PART",
                        "item_no": "3001",
                        "condition": "NEW",
                        "qty_ordered": 2,
                        "unit_price": "0.10",
                        "line_total": "0.20",
                    }
                ],
            },
        )
        assert create_resp.status_code == 201
        order = create_resp.json()

        list_resp = await ac.get("/api/v1/orders", params={"q": "BL-1001"})
        assert list_resp.status_code == 200
        assert list_resp.json()

        lines_resp = await ac.get(f"/api/v1/orders/{order['id']}/lines")
        assert lines_resp.status_code == 200
        assert lines_resp.json()[0]["item_no"] == "3001"

        status_resp = await ac.post(
            f"/api/v1/orders/{order['id']}/status",
            json={"status": "PENDING", "notes": "Payment confirmed"},
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "PENDING"

        invalid_resp = await ac.post(
            f"/api/v1/orders/{order['id']}/status",
            json={"status": "SHIPPED"},
        )
        assert invalid_resp.status_code == 400

        history_resp = await ac.get(f"/api/v1/orders/{order['id']}/history")
        assert history_resp.status_code == 200
        assert len(history_resp.json()) >= 2
