from __future__ import annotations

from app.integrations.base import InventoryAdapter
from app.integrations.mock import MockInventoryAdapter
from app.modules.stores.models import Store
from sqlalchemy.ext.asyncio import AsyncSession


def get_inventory_adapter(db: AsyncSession, store: Store) -> InventoryAdapter:
    if store.channel in {"bricklink", "brickowl", "brikick", "local", "shopify", "ebay", "etsy"}:
        return MockInventoryAdapter(db, store)
    return MockInventoryAdapter(db, store)
