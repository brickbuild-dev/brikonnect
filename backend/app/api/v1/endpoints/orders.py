from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.order import Order

router = APIRouter()

@router.get("/")
async def list_orders(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Order).where(Order.tenant_id == user.tenant_id).order_by(Order.created_at.desc()).limit(200)
    rows = (await db.execute(q)).scalars().all()
    return {"items": [
        {
            "id": r.id,
            "order_no": r.order_no,
            "status": r.status,
            "buyer_name": r.buyer_name,
            "buyer_email": r.buyer_email,
            "total_cents": r.total_cents,
            "currency": r.currency,
            "created_at": r.created_at,
        } for r in rows
    ]}
