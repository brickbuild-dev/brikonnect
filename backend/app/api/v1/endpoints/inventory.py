from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.inventory import InventoryLot

router = APIRouter()

@router.get("/lots")
async def list_lots(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(InventoryLot).where(InventoryLot.tenant_id == user.tenant_id).limit(200)
    rows = (await db.execute(q)).scalars().all()
    return {"items": [
        {
            "id": r.id,
            "sku": r.sku,
            "item_type": r.item_type,
            "item_no": r.item_no,
            "color_id": r.color_id,
            "condition": r.condition,
            "qty_available": r.qty_available,
            "price_cents": r.price_cents,
            "currency": r.currency,
            "location": r.location,
        } for r in rows
    ]}

@router.post("/lots")
async def create_lot(payload: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Minimal stub; replace with proper schema + validation
    lot = InventoryLot(
        tenant_id=user.tenant_id,
        sku=payload.get("sku"),
        item_type=payload.get("item_type", "PART"),
        item_no=payload.get("item_no"),
        color_id=payload.get("color_id"),
        condition=payload.get("condition", "USED"),
        qty_available=int(payload.get("qty_available", 0)),
        price_cents=payload.get("price_cents"),
        currency=payload.get("currency"),
        location=payload.get("location"),
    )
    db.add(lot)
    await db.commit()
    await db.refresh(lot)
    return {"ok": True, "id": lot.id}
