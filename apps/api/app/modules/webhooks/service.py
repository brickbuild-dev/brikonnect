from __future__ import annotations

import secrets

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.service import create_event
from app.modules.webhooks.models import Webhook, WebhookDelivery
from app.modules.webhooks.schemas import WebhookCreate, WebhookUpdate


async def list_webhooks(db: AsyncSession, tenant_id) -> list[Webhook]:
    result = await db.execute(select(Webhook).where(Webhook.tenant_id == tenant_id))
    return list(result.scalars().all())


async def get_webhook(db: AsyncSession, tenant_id, webhook_id) -> Webhook | None:
    result = await db.execute(
        select(Webhook).where(Webhook.tenant_id == tenant_id, Webhook.id == webhook_id)
    )
    return result.scalar_one_or_none()


async def create_webhook(db: AsyncSession, tenant_id, payload: WebhookCreate) -> Webhook:
    secret = payload.secret or secrets.token_hex(16)
    webhook = Webhook(
        tenant_id=tenant_id,
        url=payload.url,
        secret=secret,
        events=payload.events,
        is_enabled=payload.is_enabled,
    )
    db.add(webhook)
    await db.flush()
    return webhook


async def update_webhook(db: AsyncSession, webhook: Webhook, payload: WebhookUpdate) -> Webhook:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(webhook, field, value)
    await db.flush()
    return webhook


async def delete_webhook(db: AsyncSession, webhook: Webhook) -> None:
    await db.execute(delete(Webhook).where(Webhook.id == webhook.id))


async def create_test_delivery(
    db: AsyncSession, tenant_id, webhook: Webhook
) -> WebhookDelivery:
    event = await create_event(db, tenant_id, "webhook.test", {"webhook_id": str(webhook.id)})
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_id=event.id,
        status="PENDING",
    )
    db.add(delivery)
    await db.flush()
    return delivery
