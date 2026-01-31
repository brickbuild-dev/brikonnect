from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BrickognizePrediction(BaseModel):
    item_no: str
    name: str | None = None
    confidence: float = Field(ge=0, le=1)
    image_url: str | None = None
    platform_ids: dict | None = None


class BrickognizeResult(BaseModel):
    image_hash: str
    predictions: list[BrickognizePrediction]
    inventory_matches: list[dict] | None = None
    cached_at: datetime | None = None
