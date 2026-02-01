from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import CatalogCategory, CatalogColor, CatalogItem
from app.modules.catalog.schemas import CatalogCategoryImport, CatalogColorImport, CatalogItemImport


def _utcnow():
    return datetime.now(timezone.utc)


async def import_colors(db: AsyncSession, colors: list[CatalogColorImport]) -> int:
    count = 0
    for color in colors:
        existing = await db.get(CatalogColor, color.id)
        payload = color.model_dump()
        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
        else:
            db.add(CatalogColor(**payload))
        count += 1
    await db.flush()
    return count


async def import_categories(db: AsyncSession, categories: list[CatalogCategoryImport]) -> int:
    count = 0
    for category in categories:
        existing = await db.get(CatalogCategory, category.id)
        payload = category.model_dump()
        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
        else:
            db.add(CatalogCategory(**payload))
        count += 1
    await db.flush()
    return count


async def import_items(db: AsyncSession, items: list[CatalogItemImport]) -> int:
    count = 0
    for item in items:
        stmt = select(CatalogItem).where(
            CatalogItem.item_type == item.item_type,
            CatalogItem.item_no == item.item_no,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        payload = item.model_dump()
        payload.setdefault("source", "bricklink")
        payload.setdefault("source_updated_at", _utcnow())
        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
        else:
            db.add(CatalogItem(**payload))
        count += 1
    await db.flush()
    return count
