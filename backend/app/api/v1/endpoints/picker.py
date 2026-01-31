from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

router = APIRouter()

@router.get("/queue")
async def queue(user=Depends(get_current_user)):
    # Replace with real pick-wave model.
    return {"items": [], "ok": True}
