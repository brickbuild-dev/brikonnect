from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogItemOut(BaseModel):
    id: UUID
    item_type: str
    item_no: str
    name: str
    category_id: int | None = None
    category_name: str | None = None
    weight_grams: Decimal | None = None
    dimensions: dict | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_released: int | None = None
    year_ended: int | None = None
    alternate_nos: list[str] | None = None
    source: str
    source_updated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CatalogColorOut(BaseModel):
    id: int
    name: str
    rgb: str | None = None
    brickowl_id: int | None = None
    rebrickable_id: int | None = None
    ldraw_id: int | None = None
    lego_ids: list[int] | None = None
    color_type: str | None = None
    source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CatalogCategoryOut(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    source: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CatalogIdMappingOut(BaseModel):
    id: UUID
    item_type: str
    canonical_item_no: str
    bricklink_id: str | None = None
    brickowl_id: str | None = None
    brikick_id: str | None = None
    rebrickable_id: str | None = None
    lego_element_ids: list[str] | None = None
    mapping_source: str | None = None
    confidence: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CatalogItemDetailOut(BaseModel):
    item: CatalogItemOut
    mappings: CatalogIdMappingOut | None = None


class CatalogColorImport(BaseModel):
    id: int
    name: str
    rgb: str | None = None
    brickowl_id: int | None = None
    rebrickable_id: int | None = None
    ldraw_id: int | None = None
    lego_ids: list[int] | None = None
    color_type: str | None = None
    source: str | None = None


class CatalogCategoryImport(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    source: str | None = None


class CatalogItemImport(BaseModel):
    item_type: str = Field(min_length=1, max_length=20)
    item_no: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=500)
    category_id: int | None = None
    category_name: str | None = None
    weight_grams: Decimal | None = None
    dimensions: dict | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_released: int | None = None
    year_ended: int | None = None
    alternate_nos: list[str] | None = None
    source: str | None = None
    source_updated_at: datetime | None = None


class CatalogImportColorsRequest(BaseModel):
    colors: list[CatalogColorImport]


class CatalogImportCategoriesRequest(BaseModel):
    categories: list[CatalogCategoryImport]


class CatalogImportItemsRequest(BaseModel):
    items: list[CatalogItemImport]


class ApiRateLimitOut(BaseModel):
    source: str
    daily_limit: int
    requests_today: int
    last_request_at: datetime | None = None
    reset_at: date | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
