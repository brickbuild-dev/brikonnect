from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.registry import get_inventory_adapter
from app.modules.rbac.deps import require_permissions
from app.modules.stores.schemas import StoreCreate, StoreCredentialsPayload, StoreOut, StoreUpdate
from app.modules.stores.service import (
    create_store,
    delete_store,
    get_store,
    list_stores,
    set_store_credentials,
    update_store,
)

router = APIRouter()


@router.get("/", response_model=list[StoreOut])
async def list_all(
    current_user=Depends(require_permissions(["stores:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_stores(db, current_user.tenant_id)


@router.post("/", response_model=StoreOut, status_code=201)
async def create(
    payload: StoreCreate,
    current_user=Depends(require_permissions(["stores:write"])),
    db: AsyncSession = Depends(get_db),
):
    store = await create_store(db, current_user.tenant_id, payload)
    await db.commit()
    return store


@router.get("/{store_id}", response_model=StoreOut)
async def get(
    store_id: UUID,
    current_user=Depends(require_permissions(["stores:read"])),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store(db, current_user.tenant_id, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.patch("/{store_id}", response_model=StoreOut)
async def update(
    store_id: UUID,
    payload: StoreUpdate,
    current_user=Depends(require_permissions(["stores:write"])),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store(db, current_user.tenant_id, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    store = await update_store(db, store, payload)
    await db.commit()
    return store


@router.delete("/{store_id}", status_code=204)
async def delete(
    store_id: UUID,
    current_user=Depends(require_permissions(["stores:write"])),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store(db, current_user.tenant_id, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    await delete_store(db, store)
    await db.commit()
    return None


@router.post("/{store_id}/credentials")
async def set_credentials(
    store_id: UUID,
    payload: StoreCredentialsPayload,
    current_user=Depends(require_permissions(["stores:credentials"])),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store(db, current_user.tenant_id, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    await set_store_credentials(db, store, payload)
    await db.commit()
    return {"ok": True}


@router.post("/{store_id}/test")
async def test_credentials(
    store_id: UUID,
    current_user=Depends(require_permissions(["stores:credentials"])),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store(db, current_user.tenant_id, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    adapter = get_inventory_adapter(db, store)
    ok = await adapter.test_connection()
    return {"ok": ok}


@router.post("/{store_id}/sync")
async def trigger_sync(
    store_id: UUID,
    current_user=Depends(require_permissions(["sync:preview"])),
    db: AsyncSession = Depends(get_db),
):
    store = await get_store(db, current_user.tenant_id, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"ok": True}
