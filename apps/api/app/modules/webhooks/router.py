from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.rbac.deps import require_permissions
from app.modules.webhooks.schemas import WebhookCreate, WebhookDeliveryOut, WebhookOut, WebhookUpdate
from app.modules.webhooks.service import (
    create_test_delivery,
    create_webhook,
    delete_webhook,
    get_webhook,
    list_webhooks,
    update_webhook,
)

router = APIRouter()


@router.get("/", response_model=list[WebhookOut])
async def list_all(
    current_user=Depends(require_permissions(["webhooks:manage"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_webhooks(db, current_user.tenant_id)


@router.post("/", response_model=WebhookOut, status_code=201)
async def create(
    payload: WebhookCreate,
    current_user=Depends(require_permissions(["webhooks:manage"])),
    db: AsyncSession = Depends(get_db),
):
    webhook = await create_webhook(db, current_user.tenant_id, payload)
    await db.commit()
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookOut)
async def update(
    webhook_id: UUID,
    payload: WebhookUpdate,
    current_user=Depends(require_permissions(["webhooks:manage"])),
    db: AsyncSession = Depends(get_db),
):
    webhook = await get_webhook(db, current_user.tenant_id, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    webhook = await update_webhook(db, webhook, payload)
    await db.commit()
    return webhook


@router.delete("/{webhook_id}", status_code=204)
async def delete(
    webhook_id: UUID,
    current_user=Depends(require_permissions(["webhooks:manage"])),
    db: AsyncSession = Depends(get_db),
):
    webhook = await get_webhook(db, current_user.tenant_id, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await delete_webhook(db, webhook)
    await db.commit()
    return None


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryOut)
async def test_webhook(
    webhook_id: UUID,
    current_user=Depends(require_permissions(["webhooks:manage"])),
    db: AsyncSession = Depends(get_db),
):
    webhook = await get_webhook(db, current_user.tenant_id, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    delivery = await create_test_delivery(db, current_user.tenant_id, webhook)
    await db.commit()
    return delivery
