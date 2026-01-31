from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def definitions():
    # Centralize enums/codes here (conditions, item_types, currencies, countries, etc.)
    return {
        "item_types": ["PART", "SET", "MINIFIG", "BOOK", "GEAR", "CATALOG", "INSTRUCTION", "ORIGINAL_BOX", "UNSORTED_LOT"],
        "conditions": ["NEW", "USED"],
        "ok": True,
    }
