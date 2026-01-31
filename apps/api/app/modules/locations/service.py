from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.locations.models import Location
from app.modules.locations.schemas import LocationCreate, LocationUpdate


async def list_locations(db: AsyncSession, tenant_id) -> list[Location]:
    result = await db.execute(
        select(Location).where(Location.tenant_id == tenant_id).order_by(Location.sort_order)
    )
    return list(result.scalars().all())


async def get_location(db: AsyncSession, tenant_id, location_id) -> Location | None:
    result = await db.execute(
        select(Location).where(Location.tenant_id == tenant_id, Location.id == location_id)
    )
    return result.scalar_one_or_none()


async def create_location(db: AsyncSession, tenant_id, payload: LocationCreate) -> Location:
    location = Location(
        tenant_id=tenant_id,
        code=payload.code,
        zone=payload.zone,
        aisle=payload.aisle,
        shelf=payload.shelf,
        bin=payload.bin,
        sort_order=payload.sort_order,
    )
    db.add(location)
    await db.flush()
    return location


async def update_location(db: AsyncSession, location: Location, payload: LocationUpdate) -> Location:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    await db.flush()
    return location


async def delete_location(db: AsyncSession, location: Location) -> None:
    await db.execute(delete(Location).where(Location.id == location.id))
