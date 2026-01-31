from __future__ import annotations

from datetime import datetime, timezone


async def search_items(query: str, item_type: str | None = None) -> list[dict]:
    if not query or not query.lower().startswith("bl-"):
        return []
    normalized = query.upper()
    return [
        {
            "item_type": item_type or "PART",
            "item_no": normalized,
            "name": f"BrickLink {normalized}",
            "category_id": None,
            "category_name": None,
            "weight_grams": None,
            "dimensions": None,
            "image_url": None,
            "thumbnail_url": None,
            "year_released": None,
            "year_ended": None,
            "alternate_nos": [],
            "source": "bricklink",
            "source_updated_at": datetime.now(timezone.utc),
            "bricklink_id": normalized,
        }
    ]
