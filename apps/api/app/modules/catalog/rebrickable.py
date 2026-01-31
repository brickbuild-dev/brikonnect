from __future__ import annotations

from datetime import datetime, timezone


async def search_items(query: str, item_type: str | None = None) -> list[dict]:
    if not query or not query.lower().startswith("fallback"):
        return []
    return [
        {
            "item_type": item_type or "PART",
            "item_no": query.upper(),
            "name": f"Fallback {query}",
            "category_id": None,
            "category_name": None,
            "weight_grams": None,
            "dimensions": None,
            "image_url": None,
            "thumbnail_url": None,
            "year_released": None,
            "year_ended": None,
            "alternate_nos": [],
            "source": "rebrickable",
            "source_updated_at": datetime.now(timezone.utc),
            "rebrickable_id": query.upper(),
        }
    ]
