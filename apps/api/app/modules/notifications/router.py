from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.notifications.schemas import NotificationOut
from app.modules.notifications.service import (
    dismiss,
    get_notification,
    list_notifications,
    mark_all_read,
    mark_read,
)
from app.modules.rbac.deps import require_permissions

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationOut])
async def list_all(
    current_user=Depends(require_permissions(["notifications:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_notifications(db, current_user.tenant_id, current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: UUID,
    current_user=Depends(require_permissions(["notifications:read"])),
    db: AsyncSession = Depends(get_db),
):
    notification = await get_notification(db, current_user.tenant_id, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = await mark_read(db, notification)
    await db.commit()
    return notification


@router.post("/read-all")
async def mark_all(
    current_user=Depends(require_permissions(["notifications:read"])),
    db: AsyncSession = Depends(get_db),
):
    count = await mark_all_read(db, current_user.tenant_id, current_user.id)
    await db.commit()
    return {"updated": count}


@router.post("/{notification_id}/dismiss", response_model=NotificationOut)
async def dismiss_notification(
    notification_id: UUID,
    current_user=Depends(require_permissions(["notifications:read"])),
    db: AsyncSession = Depends(get_db),
):
    notification = await get_notification(db, current_user.tenant_id, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = await dismiss(db, notification)
    await db.commit()
    return notification
