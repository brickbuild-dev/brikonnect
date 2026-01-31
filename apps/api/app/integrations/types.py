from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class AdapterInventoryItem(BaseModel):
    external_id: str
    item_type: str = Field(min_length=1, max_length=20)
    item_no: str = Field(min_length=1, max_length=64)
    color_id: int | None = None
    condition: str = Field(min_length=1, max_length=10)
    qty_available: int = 0
    unit_price: Decimal | None = None
    remarks: str | None = None

    def key(self) -> tuple[str, str, int | None, str]:
        return (self.item_type, self.item_no, self.color_id, self.condition)

    def to_state(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
