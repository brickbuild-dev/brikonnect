from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event


async def create_event(db: AsyncSession, tenant_id, event_type: str, payload: dict) -> Event:
    event = Event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    db.add(event)
    await db.flush()
    return event
