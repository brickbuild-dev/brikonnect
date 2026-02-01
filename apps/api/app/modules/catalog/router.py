from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.catalog.importer import import_categories, import_colors, import_items
from app.modules.catalog.schemas import (
    CatalogCategoryOut,
    CatalogImportCategoriesRequest,
    CatalogImportColorsRequest,
    CatalogImportItemsRequest,
    CatalogItemDetailOut,
    CatalogItemOut,
    CatalogColorOut,
)
from app.modules.catalog.service import (
    get_item,
    get_mapping,
    list_categories,
    list_colors,
    search_items,
)
from app.modules.rbac.deps import require_permissions

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/search", response_model=list[CatalogItemOut])
async def search(
    q: str,
    item_type: str | None = None,
    platform_id: str | None = None,
    current_user=Depends(require_permissions(["catalog:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await search_items(db, q, item_type=item_type, platform_id=platform_id)


@router.get("/items/{item_type}/{item_no}", response_model=CatalogItemDetailOut)
async def item_detail(
    item_type: str,
    item_no: str,
    current_user=Depends(require_permissions(["catalog:read"])),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item(db, item_type, item_no)
    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    mapping = await get_mapping(db, item_type, item_no)
    return {"item": item, "mappings": mapping}


@router.get("/colors", response_model=list[CatalogColorOut])
async def colors(
    current_user=Depends(require_permissions(["catalog:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_colors(db)


@router.get("/categories", response_model=list[CatalogCategoryOut])
async def categories(
    current_user=Depends(require_permissions(["catalog:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_categories(db)


@router.post("/import/colors")
async def import_color_dump(
    payload: CatalogImportColorsRequest,
    current_user=Depends(require_permissions(["catalog:import"])),
    db: AsyncSession = Depends(get_db),
):
    count = await import_colors(db, payload.colors)
    await db.commit()
    return {"imported": count}


@router.post("/import/categories")
async def import_category_dump(
    payload: CatalogImportCategoriesRequest,
    current_user=Depends(require_permissions(["catalog:import"])),
    db: AsyncSession = Depends(get_db),
):
    count = await import_categories(db, payload.categories)
    await db.commit()
    return {"imported": count}


@router.post("/import/items")
async def import_item_dump(
    payload: CatalogImportItemsRequest,
    current_user=Depends(require_permissions(["catalog:import"])),
    db: AsyncSession = Depends(get_db),
):
    count = await import_items(db, payload.items)
    await db.commit()
    return {"imported": count}
