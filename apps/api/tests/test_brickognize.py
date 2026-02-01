from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.modules.brickognize.models import BrickognizeCache
from app.modules.brickognize.service import identify_part, search_by_image
from app.modules.catalog.models import CatalogIdMapping, CatalogItem
from app.modules.inventory.schemas import InventoryItemCreate
from app.modules.inventory.service import create_item
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant


@pytest.mark.asyncio
async def test_identify_caches_result(db_session):
    image_bytes = b"item:3001"
    result = await identify_part(db_session, image_bytes)
    assert result.predictions

    count_stmt = select(func.count()).select_from(BrickognizeCache)
    count = (await db_session.execute(count_stmt)).scalar_one()
    assert count == 1

    result_again = await identify_part(db_session, image_bytes)
    count_again = (await db_session.execute(count_stmt)).scalar_one()
    assert count_again == 1
    assert result_again.predictions[0].item_no == result.predictions[0].item_no


@pytest.mark.asyncio
async def test_identify_maps_to_catalog(db_session):
    db_session.add(
        CatalogItem(
            item_type="PART",
            item_no="3001",
            name="Brick 2x4",
            source="bricklink",
            source_updated_at=datetime.now(timezone.utc),
        )
    )
    db_session.add(
        CatalogIdMapping(
            item_type="PART",
            canonical_item_no="3001",
            bricklink_id="BL-3001",
        )
    )
    await db_session.commit()

    result = await identify_part(db_session, b"item:3001")
    assert result.predictions[0].name == "Brick 2x4"
    assert result.predictions[0].platform_ids["bricklink"] == "BL-3001"


@pytest.mark.asyncio
async def test_search_by_image(db_session):
    tenant = await create_tenant(db_session, TenantCreate(slug="brickognize", name="Brickognize"))
    payload = InventoryItemCreate(
        item_type="PART",
        item_no="3001",
        color_id=None,
        condition="NEW",
        qty_available=5,
        qty_reserved=0,
        unit_price=None,
        currency="EUR",
        cost_basis=None,
        description="Brick 2x4",
        remarks=None,
        is_retain=False,
        is_stock_room=False,
        locations=[],
    )
    item = await create_item(db_session, tenant.id, payload)
    await db_session.commit()

    result = await search_by_image(db_session, tenant.id, b"item:3001")
    assert result.inventory_matches
    assert result.inventory_matches[0]["id"] == str(item.id)
