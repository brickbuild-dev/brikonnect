from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.shipping.base import Address, Package, ShipmentRequest
from app.integrations.shipping.registry import get_adapter
from app.modules.orders.models import Order
from app.modules.shipping.models import Shipment, ShippingCarrierConfig


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_address(ship_to: dict | None, fallback_name: str | None = None) -> Address:
    data = ship_to or {}
    return Address(
        name=data.get("name") or fallback_name,
        line1=data.get("address1") or data.get("line1"),
        city=data.get("city"),
        country=data.get("country"),
        postal_code=data.get("postal_code") or data.get("zip"),
    )


def _build_package(order: Order) -> Package:
    return Package(weight_grams=500, length_cm=20, width_cm=15, height_cm=5)


async def list_carriers(db: AsyncSession, tenant_id) -> list[ShippingCarrierConfig]:
    stmt = select(ShippingCarrierConfig).where(ShippingCarrierConfig.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def upsert_carrier(
    db: AsyncSession,
    tenant_id,
    carrier_code: str,
    credentials: dict | None,
    is_enabled: bool,
) -> ShippingCarrierConfig:
    stmt = select(ShippingCarrierConfig).where(
        ShippingCarrierConfig.tenant_id == tenant_id,
        ShippingCarrierConfig.carrier_code == carrier_code,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.credentials = credentials
        existing.is_enabled = is_enabled
        await db.flush()
        return existing
    config = ShippingCarrierConfig(
        tenant_id=tenant_id,
        carrier_code=carrier_code,
        credentials=credentials,
        is_enabled=is_enabled,
    )
    db.add(config)
    await db.flush()
    return config


async def _get_order(db: AsyncSession, tenant_id, order_id) -> Order:
    stmt = select(Order).where(Order.tenant_id == tenant_id, Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise ValueError("Order not found")
    return order


async def get_rates(
    db: AsyncSession,
    tenant_id,
    order_id,
    carrier_codes: list[str] | None = None,
):
    order = await _get_order(db, tenant_id, order_id)
    configs = await list_carriers(db, tenant_id)
    enabled_codes = [c.carrier_code for c in configs if c.is_enabled]
    codes = carrier_codes or enabled_codes
    if not codes:
        return []

    destination = _build_address(order.ship_to, fallback_name=order.buyer_name)
    origin = Address(name="Warehouse", line1="Warehouse", city="Lisbon", country="PT", postal_code="0000")
    package = _build_package(order)

    rates = []
    for code in codes:
        adapter = get_adapter(code)
        rates.extend(await adapter.get_rates(package, origin, destination))
    return rates


async def create_label(
    db: AsyncSession,
    tenant_id,
    order_id,
    carrier_code: str,
    service_level: str,
) -> Shipment:
    order = await _get_order(db, tenant_id, order_id)
    config_stmt = select(ShippingCarrierConfig).where(
        ShippingCarrierConfig.tenant_id == tenant_id,
        ShippingCarrierConfig.carrier_code == carrier_code,
        ShippingCarrierConfig.is_enabled.is_(True),
    )
    config = (await db.execute(config_stmt)).scalar_one_or_none()
    if not config:
        raise ValueError("Carrier not configured")

    destination = _build_address(order.ship_to, fallback_name=order.buyer_name)
    origin = Address(name="Warehouse", line1="Warehouse", city="Lisbon", country="PT", postal_code="0000")
    package = _build_package(order)
    adapter = get_adapter(carrier_code)
    response = await adapter.create_label(
        ShipmentRequest(
            order_id=str(order.id),
            package=package,
            origin=origin,
            destination=destination,
            service_level=service_level,
        )
    )

    shipment = Shipment(
        tenant_id=tenant_id,
        order_id=order.id,
        carrier_code=carrier_code,
        service_level=service_level,
        status=response.status,
        label_url=response.label_url,
        tracking_number=response.tracking_number,
        rate_amount=None,
        currency=None,
    )
    db.add(shipment)
    await db.flush()
    return shipment


async def get_shipment(db: AsyncSession, tenant_id, shipment_id) -> Shipment | None:
    stmt = select(Shipment).where(Shipment.tenant_id == tenant_id, Shipment.id == shipment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def track_shipment(db: AsyncSession, carrier_code: str, tracking_number: str):
    adapter = get_adapter(carrier_code)
    return await adapter.track(tracking_number)


async def cancel_shipment(db: AsyncSession, shipment: Shipment) -> Shipment:
    adapter = get_adapter(shipment.carrier_code)
    await adapter.cancel(str(shipment.id))
    shipment.status = "CANCELLED"
    shipment.updated_at = _utcnow()
    await db.flush()
    return shipment
