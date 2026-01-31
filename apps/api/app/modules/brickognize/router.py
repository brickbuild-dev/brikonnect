from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.brickognize.schemas import BrickognizeResult
from app.modules.brickognize.service import identify_part, search_by_image
from app.modules.rbac.deps import require_permissions

router = APIRouter(prefix="/brickognize", tags=["brickognize"])


@router.post("/identify", response_model=BrickognizeResult)
async def identify(
    image: UploadFile,
    current_user=Depends(require_permissions(["brickognize:use"])),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await image.read()
    return await identify_part(db, image_bytes)


@router.post("/search/image", response_model=BrickognizeResult)
async def search_image(
    image: UploadFile,
    current_user=Depends(require_permissions(["brickognize:use"])),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await image.read()
    return await search_by_image(db, current_user.tenant_id, image_bytes)
