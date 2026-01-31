from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.locations.schemas import LocationCreate, LocationOut, LocationUpdate
from app.modules.locations.service import (
    create_location,
    delete_location,
    get_location,
    list_locations,
    update_location,
)
from app.modules.rbac.deps import require_permissions

router = APIRouter()


@router.get("/", response_model=list[LocationOut])
async def list_all(
    current_user=Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_locations(db, current_user.tenant_id)


@router.post("/", response_model=LocationOut, status_code=201)
async def create(
    payload: LocationCreate,
    current_user=Depends(require_permissions(["inventory:write"])),
    db: AsyncSession = Depends(get_db),
):
    location = await create_location(db, current_user.tenant_id, payload)
    await db.commit()
    return location


@router.patch("/{location_id}", response_model=LocationOut)
async def update(
    location_id: UUID,
    payload: LocationUpdate,
    current_user=Depends(require_permissions(["inventory:write"])),
    db: AsyncSession = Depends(get_db),
):
    location = await get_location(db, current_user.tenant_id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    location = await update_location(db, location, payload)
    await db.commit()
    return location


@router.delete("/{location_id}", status_code=204)
async def delete(
    location_id: UUID,
    current_user=Depends(require_permissions(["inventory:delete"])),
    db: AsyncSession = Depends(get_db),
):
    location = await get_location(db, current_user.tenant_id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    await delete_location(db, location)
    await db.commit()
    return Response(status_code=204)
