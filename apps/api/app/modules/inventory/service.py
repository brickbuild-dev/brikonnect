from __future__ import annotations

from typing import Iterable

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.inventory.models import InventoryItem, InventoryItemLocation
from app.modules.inventory.schemas import InventoryBulkItem, InventoryItemCreate, InventoryItemUpdate
from app.modules.locations.models import Location


class InventoryVersionConflict(Exception):
    pass


class InventoryValidationError(Exception):
    pass


def _validate_required_for_create(payload: InventoryBulkItem) -> None:
    if not payload.item_type or not payload.item_no or not payload.condition:
        raise InventoryValidationError("Missing required fields for new inventory item.")


async def list_items(
    db: AsyncSession,
    tenant_id,
    item_type: str | None = None,
    item_no: str | None = None,
    condition: str | None = None,
    q: str | None = None,
) -> list[InventoryItem]:
    stmt = (
        select(InventoryItem)
        .where(InventoryItem.tenant_id == tenant_id)
        .options(
            selectinload(InventoryItem.locations).selectinload(InventoryItemLocation.location)
        )
        .order_by(InventoryItem.created_at.desc())
    )
    if item_type:
        stmt = stmt.where(InventoryItem.item_type == item_type)
    if item_no:
        stmt = stmt.where(InventoryItem.item_no == item_no)
    if condition:
        stmt = stmt.where(InventoryItem.condition == condition)
    if q:
        stmt = stmt.where(
            or_(
                InventoryItem.item_no.ilike(f"%{q}%"),
                InventoryItem.description.ilike(f"%{q}%"),
            )
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_item(db: AsyncSession, tenant_id, item_id) -> InventoryItem | None:
    stmt = (
        select(InventoryItem)
        .where(InventoryItem.tenant_id == tenant_id, InventoryItem.id == item_id)
        .options(
            selectinload(InventoryItem.locations).selectinload(InventoryItemLocation.location)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _resolve_locations(
    db: AsyncSession, tenant_id, location_ids: Iterable
) -> dict:
    if not location_ids:
        return {}
    result = await db.execute(
        select(Location).where(Location.tenant_id == tenant_id, Location.id.in_(location_ids))
    )
    locations = list(result.scalars().all())
    if len(locations) != len(set(location_ids)):
        raise InventoryValidationError("One or more locations were not found for tenant.")
    return {location.id: location for location in locations}


async def _set_item_locations(
    db: AsyncSession,
    item: InventoryItem,
    tenant_id,
    locations: list,
) -> None:
    location_map = await _resolve_locations(db, tenant_id, [l.location_id for l in locations])
    await db.execute(
        delete(InventoryItemLocation).where(
            InventoryItemLocation.inventory_item_id == item.id
        )
    )
    for payload in locations:
        if payload.location_id not in location_map:
            continue
        db.add(
            InventoryItemLocation(
                inventory_item_id=item.id,
                location_id=payload.location_id,
                qty=payload.qty,
            )
        )


async def create_item(
    db: AsyncSession,
    tenant_id,
    payload: InventoryItemCreate,
) -> InventoryItem:
    item = InventoryItem(
        tenant_id=tenant_id,
        item_type=payload.item_type,
        item_no=payload.item_no,
        color_id=payload.color_id,
        condition=payload.condition,
        qty_available=payload.qty_available,
        qty_reserved=payload.qty_reserved,
        unit_price=payload.unit_price,
        currency=payload.currency,
        cost_basis=payload.cost_basis,
        description=payload.description,
        remarks=payload.remarks,
        is_retain=payload.is_retain,
        is_stock_room=payload.is_stock_room,
    )
    db.add(item)
    await db.flush()

    if payload.locations:
        await _set_item_locations(db, item, tenant_id, payload.locations)
    await db.flush()
    return item


async def update_item(
    db: AsyncSession,
    item: InventoryItem,
    tenant_id,
    payload: InventoryItemUpdate,
) -> InventoryItem:
    if payload.version is not None and payload.version != item.version:
        raise InventoryVersionConflict("Inventory item version mismatch.")

    data = payload.model_dump(exclude_unset=True, exclude={"locations", "version"})
    for field, value in data.items():
        setattr(item, field, value)

    if payload.locations is not None:
        await _set_item_locations(db, item, tenant_id, payload.locations)

    if data or payload.locations is not None:
        item.version += 1

    await db.flush()
    return item


async def delete_item(db: AsyncSession, item: InventoryItem) -> None:
    await db.execute(delete(InventoryItem).where(InventoryItem.id == item.id))


async def bulk_upsert(
    db: AsyncSession,
    tenant_id,
    items: list[InventoryBulkItem],
) -> list[InventoryItem]:
    results: list[InventoryItem] = []
    for payload in items:
        if payload.id:
            item = await get_item(db, tenant_id, payload.id)
            if not item:
                raise InventoryValidationError("Inventory item not found for update.")
            update_payload = InventoryItemUpdate(
                **payload.model_dump(exclude={"id"}, exclude_unset=True)
            )
            item = await update_item(db, item, tenant_id, update_payload)
            results.append(item)
        else:
            _validate_required_for_create(payload)
            create_payload = InventoryItemCreate(
                **payload.model_dump(exclude={"id"}, exclude_unset=True)
            )
            item = await create_item(db, tenant_id, create_payload)
            results.append(item)
    return results
