from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.brickognize.models import BrickognizeCache
from app.modules.brickognize.schemas import BrickognizePrediction, BrickognizeResult
from app.modules.catalog.models import CatalogItem
from app.modules.catalog.service import get_mapping
from app.modules.inventory import service as inventory_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _extract_item_no(image_bytes: bytes, image_hash: str) -> str:
    try:
        text = image_bytes.decode("utf-8")
        if text.startswith("item:"):
            return text.split("item:", 1)[1].strip()
    except UnicodeDecodeError:
        pass
    return image_hash[:8].upper()


async def _mock_predictions(image_bytes: bytes, image_hash: str) -> list[dict]:
    item_no = _extract_item_no(image_bytes, image_hash)
    return [
        {
            "item_no": item_no,
            "name": None,
            "confidence": 0.92,
            "image_url": None,
            "platform_ids": None,
        }
    ]


async def identify_part(db: AsyncSession, image_bytes: bytes) -> BrickognizeResult:
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    stmt = select(BrickognizeCache).where(BrickognizeCache.image_hash == image_hash)
    cached = (await db.execute(stmt)).scalar_one_or_none()
    if cached:
        return BrickognizeResult(
            image_hash=image_hash,
            predictions=[BrickognizePrediction(**p) for p in cached.predictions],
            cached_at=cached.created_at,
        )

    predictions = await _mock_predictions(image_bytes, image_hash)
    matched_catalog_id = None
    for prediction in predictions:
        item_no = prediction["item_no"]
        item = await db.execute(
            select(CatalogItem).where(CatalogItem.item_no == item_no)
        )
        catalog_item = item.scalar_one_or_none()
        if catalog_item:
            prediction["name"] = catalog_item.name
            mapping = await get_mapping(db, catalog_item.item_type, catalog_item.item_no)
            if mapping:
                prediction["platform_ids"] = {
                    "bricklink": mapping.bricklink_id,
                    "brickowl": mapping.brickowl_id,
                    "brikick": mapping.brikick_id,
                    "rebrickable": mapping.rebrickable_id,
                }
            if matched_catalog_id is None:
                matched_catalog_id = catalog_item.id

    cache_entry = BrickognizeCache(
        image_hash=image_hash,
        predictions=predictions,
        top_prediction_item_no=predictions[0]["item_no"] if predictions else None,
        top_prediction_confidence=predictions[0]["confidence"] if predictions else None,
        matched_catalog_item_id=matched_catalog_id,
    )
    db.add(cache_entry)
    await db.flush()
    return BrickognizeResult(
        image_hash=image_hash,
        predictions=[BrickognizePrediction(**p) for p in predictions],
        cached_at=_utcnow(),
    )


async def search_by_image(
    db: AsyncSession,
    tenant_id,
    image_bytes: bytes,
) -> BrickognizeResult:
    result = await identify_part(db, image_bytes)
    if not result.predictions:
        return result
    top_item = result.predictions[0]
    items = await inventory_service.list_items(db, tenant_id, item_no=top_item.item_no)
    result.inventory_matches = [
        {"id": str(item.id), "item_no": item.item_no, "qty_available": item.qty_available}
        for item in items
    ]
    return result
