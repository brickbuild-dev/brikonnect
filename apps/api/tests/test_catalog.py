from datetime import datetime, timezone

import pytest

from app.modules.catalog.models import ApiRateLimit, CatalogIdMapping, CatalogItem
from app.modules.catalog.service import search_items


@pytest.mark.asyncio
async def test_multi_reference_search(db_session):
    item = CatalogItem(
        item_type="PART",
        item_no="3001",
        name="Brick 2x4",
        source="bricklink",
        source_updated_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.add(
        CatalogIdMapping(
            item_type="PART",
            canonical_item_no="3001",
            bricklink_id="BL-3001",
            rebrickable_id="RB-3001",
        )
    )
    await db_session.commit()

    results = await search_items(db_session, "BL-3001")
    assert results
    assert results[0].item_no == "3001"


@pytest.mark.asyncio
async def test_cache_hit(db_session):
    item = CatalogItem(
        item_type="PART",
        item_no="CACHE-1",
        name="Cache Brick",
        source="bricklink",
        source_updated_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    await db_session.commit()

    results = await search_items(db_session, "Cache")
    assert results
    rate_limit = await db_session.get(ApiRateLimit, "bricklink")
    assert rate_limit is None


@pytest.mark.asyncio
async def test_api_fallback(db_session):
    results = await search_items(db_session, "fallback-123")
    await db_session.commit()
    assert results
    assert results[0].item_no == "FALLBACK-123"


@pytest.mark.asyncio
async def test_rate_limit_tracking(db_session):
    results = await search_items(db_session, "bl-5000")
    await db_session.commit()
    assert results
    rate_limit = await db_session.get(ApiRateLimit, "bricklink")
    assert rate_limit is not None
    assert rate_limit.requests_today == 1
