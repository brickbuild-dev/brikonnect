from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

router = APIRouter()

@router.get("/")
async def list_notifications(user=Depends(get_current_user)):
    return {"items": [], "ok": True}
