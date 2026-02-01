from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.audit.deps import get_audit_context
from app.modules.audit.service import create_audit_log, serialize_model
from app.modules.inventory.schemas import (
    InventoryBulkRequest,
    InventoryItemCreate,
    InventoryItemOut,
    InventoryItemUpdate,
)
from app.modules.inventory.service import (
    InventoryValidationError,
    InventoryVersionConflict,
    bulk_upsert,
    create_item,
    delete_item,
    get_item,
    list_items,
    update_item,
)
from app.modules.jobs.schemas import JobOut
from app.modules.jobs.service import create_job
from app.modules.rbac.deps import require_permissions

router = APIRouter()


@router.get("/", response_model=list[InventoryItemOut])
async def list_inventory(
    item_type: str | None = None,
    item_no: str | None = None,
    condition: str | None = None,
    q: str | None = None,
    current_user=Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_items(db, current_user.tenant_id, item_type, item_no, condition, q)


@router.post("/", response_model=InventoryItemOut, status_code=201)
async def create_inventory(
    payload: InventoryItemCreate,
    current_user=Depends(require_permissions(["inventory:write"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_item(db, current_user.tenant_id, payload)
    except InventoryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await create_audit_log(
        db,
        ctx,
        action="inventory.create",
        entity_type="inventory_item",
        entity_id=item.id,
        before_state=None,
        after_state=serialize_model(item, exclude={"locations"}),
    )
    await db.commit()
    item = await get_item(db, current_user.tenant_id, item.id)
    return item


@router.get("/export")
async def export_inventory(
    current_user=Depends(require_permissions(["inventory:export"])),
    db: AsyncSession = Depends(get_db),
):
    items = await list_items(db, current_user.tenant_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["item_type", "item_no", "color_id", "condition", "qty_available", "unit_price"])
    for item in items:
        writer.writerow(
            [
                item.item_type,
                item.item_no,
                item.color_id or "",
                item.condition,
                item.qty_available,
                item.unit_price or "",
            ]
        )
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"},
    )


@router.get("/{item_id}", response_model=InventoryItemOut)
async def get_inventory(
    item_id: UUID,
    current_user=Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item(db, current_user.tenant_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.patch("/{item_id}", response_model=InventoryItemOut)
async def update_inventory(
    item_id: UUID,
    payload: InventoryItemUpdate,
    current_user=Depends(require_permissions(["inventory:write"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item(db, current_user.tenant_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    before_state = serialize_model(item, exclude={"locations"})
    try:
        item = await update_item(db, item, current_user.tenant_id, payload)
    except InventoryVersionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InventoryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await create_audit_log(
        db,
        ctx,
        action="inventory.update",
        entity_type="inventory_item",
        entity_id=item.id,
        before_state=before_state,
        after_state=serialize_model(item, exclude={"locations"}),
    )
    await db.commit()
    item = await get_item(db, current_user.tenant_id, item.id)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_inventory(
    item_id: UUID,
    current_user=Depends(require_permissions(["inventory:delete"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item(db, current_user.tenant_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    before_state = serialize_model(item, exclude={"locations"})
    await delete_item(db, item)
    await create_audit_log(
        db,
        ctx,
        action="inventory.delete",
        entity_type="inventory_item",
        entity_id=item.id,
        before_state=before_state,
        after_state=None,
    )
    await db.commit()
    return Response(status_code=204)


@router.post("/bulk", response_model=list[InventoryItemOut])
async def bulk_inventory(
    payload: InventoryBulkRequest,
    current_user=Depends(require_permissions(["inventory:write"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        items = await bulk_upsert(db, current_user.tenant_id, payload.items)
    except InventoryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InventoryVersionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await db.commit()
    hydrated = []
    for item in items:
        hydrated_item = await get_item(db, current_user.tenant_id, item.id)
        if hydrated_item:
            hydrated.append(hydrated_item)
    return hydrated


@router.post("/import", response_model=JobOut)
async def import_inventory(
    current_user=Depends(require_permissions(["inventory:import"])),
    db: AsyncSession = Depends(get_db),
):
    job = await create_job(
        db,
        current_user.tenant_id,
        job_type="inventory_import",
        created_by=current_user.id,
    )
    await db.commit()
    return job
