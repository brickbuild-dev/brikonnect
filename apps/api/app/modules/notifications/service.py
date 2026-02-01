from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def list_notifications(db: AsyncSession, tenant_id, user_id) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.tenant_id == tenant_id, Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_notification(db: AsyncSession, tenant_id, user_id, notification_id) -> Notification | None:
    stmt = select(Notification).where(
        Notification.tenant_id == tenant_id,
        Notification.user_id == user_id,
        Notification.id == notification_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def mark_read(db: AsyncSession, notification: Notification) -> Notification:
    if notification.read_at is None:
        notification.read_at = _utcnow()
    await db.flush()
    return notification


async def mark_all_read(db: AsyncSession, tenant_id, user_id) -> int:
    stmt = (
        update(Notification)
        .where(Notification.tenant_id == tenant_id, Notification.user_id == user_id)
        .values(read_at=_utcnow())
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount or 0


async def dismiss(db: AsyncSession, notification: Notification) -> Notification:
    notification.dismissed_at = _utcnow()
    await db.flush()
    return notification
