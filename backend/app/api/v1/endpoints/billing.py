from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

router = APIRouter()

@router.get("/")
async def billing(user=Depends(get_current_user)):
    return {"plan": "FREE", "ok": True}
