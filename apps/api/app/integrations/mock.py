from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.types import AdapterInventoryItem
from app.modules.stores.models import Store


class MockInventoryAdapter:
    def __init__(self, db: AsyncSession, store: Store) -> None:
        self.db = db
        self.store = store

    async def fetch_inventory(self) -> list[AdapterInventoryItem]:
        raw_items = (self.store.settings or {}).get("mock_inventory", [])
        items: list[AdapterInventoryItem] = []
        for raw in raw_items:
            data = dict(raw)
            if not data.get("external_id"):
                data["external_id"] = f"mock-{uuid.uuid4()}"
            items.append(AdapterInventoryItem.model_validate(data))
        return items

    async def apply_change(self, action: str, item: AdapterInventoryItem) -> AdapterInventoryItem:
        raw_items = list((self.store.settings or {}).get("mock_inventory", []))
        updated: list[dict[str, Any]] = []
        match_index = None
        for idx, raw in enumerate(raw_items):
            if raw.get("external_id") == item.external_id:
                match_index = idx
                break
        if match_index is None:
            for idx, raw in enumerate(raw_items):
                if (
                    raw.get("item_type"),
                    raw.get("item_no"),
                    raw.get("color_id"),
                    raw.get("condition"),
                ) == item.key():
                    match_index = idx
                    break

        if action == "ADD":
            updated = raw_items + [item.to_state()]
        elif action == "UPDATE":
            if match_index is None:
                updated = raw_items + [item.to_state()]
            else:
                updated = raw_items[:]
                updated[match_index] = item.to_state()
        elif action == "REMOVE":
            updated = [raw for idx, raw in enumerate(raw_items) if idx != match_index]
        else:
            updated = raw_items

        self.store.settings = {**(self.store.settings or {}), "mock_inventory": updated}
        await self.db.flush()
        return item

    async def test_connection(self) -> bool:
        return True
