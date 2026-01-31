from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog import bricklink, rebrickable
from app.modules.catalog.models import (
    ApiRateLimit,
    CatalogCategory,
    CatalogColor,
    CatalogIdMapping,
    CatalogItem,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _record_rate_limit(db: AsyncSession, source: str, daily_limit: int = 1000) -> None:
    today = date.today()
    rate = await db.get(ApiRateLimit, source)
    if not rate:
        rate = ApiRateLimit(source=source, daily_limit=daily_limit, requests_today=0, reset_at=today)
        db.add(rate)
    if rate.reset_at != today:
        rate.requests_today = 0
        rate.reset_at = today
    rate.requests_today += 1
    rate.last_request_at = _utcnow()
    rate.updated_at = _utcnow()
    await db.flush()


async def list_items(db: AsyncSession, item_type: str | None = None) -> list[CatalogItem]:
    stmt = select(CatalogItem)
    if item_type:
        stmt = stmt.where(CatalogItem.item_type == item_type)
    result = await db.execute(stmt.order_by(CatalogItem.name.asc()))
    return list(result.scalars().all())


async def list_colors(db: AsyncSession) -> list[CatalogColor]:
    result = await db.execute(select(CatalogColor).order_by(CatalogColor.id.asc()))
    return list(result.scalars().all())


async def list_categories(db: AsyncSession) -> list[CatalogCategory]:
    result = await db.execute(select(CatalogCategory).order_by(CatalogCategory.id.asc()))
    return list(result.scalars().all())


async def get_item(db: AsyncSession, item_type: str, item_no: str) -> CatalogItem | None:
    stmt = select(CatalogItem).where(
        CatalogItem.item_type == item_type,
        CatalogItem.item_no == item_no,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_mapping(db: AsyncSession, item_type: str, item_no: str) -> CatalogIdMapping | None:
    stmt = select(CatalogIdMapping).where(
        CatalogIdMapping.item_type == item_type,
        CatalogIdMapping.canonical_item_no == item_no,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_mappings(
    db: AsyncSession,
    query: str,
    item_type: str | None,
    platform_id: str | None,
) -> list[CatalogIdMapping]:
    stmt = select(CatalogIdMapping)
    if item_type:
        stmt = stmt.where(CatalogIdMapping.item_type == item_type)
    if platform_id == "bricklink":
        stmt = stmt.where(CatalogIdMapping.bricklink_id == query)
    elif platform_id == "brickowl":
        stmt = stmt.where(CatalogIdMapping.brickowl_id == query)
    elif platform_id == "brikick":
        stmt = stmt.where(CatalogIdMapping.brikick_id == query)
    elif platform_id == "rebrickable":
        stmt = stmt.where(CatalogIdMapping.rebrickable_id == query)
    else:
        stmt = stmt.where(
            or_(
                CatalogIdMapping.bricklink_id == query,
                CatalogIdMapping.brickowl_id == query,
                CatalogIdMapping.brikick_id == query,
                CatalogIdMapping.rebrickable_id == query,
            )
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _find_items_by_name(
    db: AsyncSession,
    query: str,
    item_type: str | None,
) -> list[CatalogItem]:
    stmt = select(CatalogItem).where(CatalogItem.name.ilike(f"%{query}%"))
    if item_type:
        stmt = stmt.where(CatalogItem.item_type == item_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _find_items_by_item_no(
    db: AsyncSession,
    query: str,
    item_type: str | None,
) -> list[CatalogItem]:
    stmt = select(CatalogItem).where(CatalogItem.item_no == query)
    if item_type:
        stmt = stmt.where(CatalogItem.item_type == item_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _cache_external_item(
    db: AsyncSession,
    item_data: dict,
) -> CatalogItem:
    stmt = select(CatalogItem).where(
        CatalogItem.item_type == item_data["item_type"],
        CatalogItem.item_no == item_data["item_no"],
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing
    item = CatalogItem(
        item_type=item_data["item_type"],
        item_no=item_data["item_no"],
        name=item_data["name"],
        category_id=item_data.get("category_id"),
        category_name=item_data.get("category_name"),
        weight_grams=item_data.get("weight_grams"),
        dimensions=item_data.get("dimensions"),
        image_url=item_data.get("image_url"),
        thumbnail_url=item_data.get("thumbnail_url"),
        year_released=item_data.get("year_released"),
        year_ended=item_data.get("year_ended"),
        alternate_nos=item_data.get("alternate_nos") or [],
        source=item_data.get("source") or "external",
        source_updated_at=item_data.get("source_updated_at"),
    )
    db.add(item)
    await db.flush()
    mapping = CatalogIdMapping(
        item_type=item.item_type,
        canonical_item_no=item.item_no,
        bricklink_id=item_data.get("bricklink_id"),
        brickowl_id=item_data.get("brickowl_id"),
        brikick_id=item_data.get("brikick_id"),
        rebrickable_id=item_data.get("rebrickable_id"),
        mapping_source=item_data.get("source"),
    )
    db.add(mapping)
    await db.flush()
    return item


async def search_items(
    db: AsyncSession,
    query: str,
    item_type: str | None = None,
    platform_id: str | None = None,
) -> list[CatalogItem]:
    if not query:
        return []

    items = await _find_items_by_item_no(db, query, item_type)
    if items:
        return items

    mappings = await _find_mappings(db, query, item_type, platform_id)
    if mappings:
        mapped_items = []
        for mapping in mappings:
            item = await get_item(db, mapping.item_type, mapping.canonical_item_no)
            if item:
                mapped_items.append(item)
        if mapped_items:
            return mapped_items

    items = await _find_items_by_name(db, query, item_type)
    if items:
        return items

    # External API fallback
    external_items = []
    bricklink_items = await bricklink.search_items(query, item_type=item_type)
    if bricklink_items:
        await _record_rate_limit(db, "bricklink")
        external_items.extend(bricklink_items)
    rebrickable_items = await rebrickable.search_items(query, item_type=item_type)
    if rebrickable_items:
        await _record_rate_limit(db, "rebrickable")
        external_items.extend(rebrickable_items)

    cached = []
    for item_data in external_items:
        cached.append(await _cache_external_item(db, item_data))
    return cached
