from __future__ import annotations

from typing import Protocol

from app.integrations.types import AdapterInventoryItem


class InventoryAdapter(Protocol):
    async def fetch_inventory(self) -> list[AdapterInventoryItem]:
        raise NotImplementedError

    async def apply_change(self, action: str, item: AdapterInventoryItem) -> AdapterInventoryItem:
        raise NotImplementedError

    async def test_connection(self) -> bool:
        raise NotImplementedError
