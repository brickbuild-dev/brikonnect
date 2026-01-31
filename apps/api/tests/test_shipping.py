from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.modules.orders.schemas import OrderCreate, OrderLineCreate
from app.modules.orders.service import create_order
from app.modules.shipping.service import create_label, get_rates, track_shipment, upsert_carrier
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant


async def _create_order(db_session, tenant_id):
    payload = OrderCreate(
        external_order_id="ORDER-1001",
        status="NEW",
        buyer_name="Shipping Buyer",
        ship_to={"name": "Buyer", "city": "Lisbon", "country": "PT", "postal_code": "0000"},
        ordered_at=datetime.now(timezone.utc),
        grand_total=Decimal("20.00"),
        currency="EUR",
        lines=[
            OrderLineCreate(
                item_type="PART",
                item_no="3001",
                condition="NEW",
                qty_ordered=2,
                unit_price=Decimal("0.10"),
                line_total=Decimal("0.20"),
            )
        ],
    )
    return await create_order(db_session, tenant_id, payload)


@pytest.mark.asyncio
async def test_get_rates_multiple_carriers(db_session):
    tenant = await create_tenant(db_session, TenantCreate(slug="shipping", name="Shipping"))
    order = await _create_order(db_session, tenant.id)
    await upsert_carrier(db_session, tenant.id, "sendcloud", credentials=None, is_enabled=True)
    await upsert_carrier(db_session, tenant.id, "pirateship", credentials=None, is_enabled=True)
    await db_session.commit()

    rates = await get_rates(db_session, tenant.id, order.id, ["sendcloud", "pirateship"])
    assert {rate.carrier_code for rate in rates} == {"sendcloud", "pirateship"}


@pytest.mark.asyncio
async def test_create_label(db_session):
    tenant = await create_tenant(db_session, TenantCreate(slug="shipping-label", name="Shipping Label"))
    order = await _create_order(db_session, tenant.id)
    await upsert_carrier(db_session, tenant.id, "sendcloud", credentials=None, is_enabled=True)
    await db_session.commit()

    shipment = await create_label(db_session, tenant.id, order.id, "sendcloud", "standard")
    assert shipment.label_url
    assert shipment.tracking_number


@pytest.mark.asyncio
async def test_track_shipment(db_session):
    tracking = await track_shipment(db_session, "shipstation", "SS123")
    assert tracking.status in {"DELIVERED", "IN_TRANSIT"}
