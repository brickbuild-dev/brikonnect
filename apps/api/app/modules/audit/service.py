from __future__ import annotations

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.inventory.models import InventoryItem
from app.modules.locations.models import Location


class AuditContext:
    def __init__(
        self,
        tenant_id,
        actor_type: str,
        actor_id=None,
        actor_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.actor_type = actor_type
        self.actor_id = actor_id
        self.actor_name = actor_name
        self.ip_address = ip_address
        self.user_agent = user_agent


def serialize_model(model, exclude: set[str] | None = None) -> dict:
    return jsonable_encoder(model, exclude=exclude or set())


async def create_audit_log(
    db: AsyncSession,
    ctx: AuditContext,
    action: str,
    entity_type: str,
    entity_id,
    before_state: dict | None,
    after_state: dict | None,
) -> AuditLog:
    audit = AuditLog(
        tenant_id=ctx.tenant_id,
        actor_type=ctx.actor_type,
        actor_id=ctx.actor_id,
        actor_name=ctx.actor_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    db.add(audit)
    await db.flush()
    return audit


async def list_audit_logs(
    db: AsyncSession, tenant_id, entity_type: str | None = None, entity_id=None
) -> list[AuditLog]:
    stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id).order_by(AuditLog.created_at.desc())
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_audit_log(db: AsyncSession, tenant_id, audit_id) -> AuditLog | None:
    result = await db.execute(
        select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.id == audit_id)
    )
    return result.scalar_one_or_none()


async def revert_audit_log(db: AsyncSession, ctx: AuditContext, audit: AuditLog) -> None:
    if not audit.before_state:
        raise ValueError("No previous state available to revert.")
    if audit.entity_type == "inventory_item":
        await _revert_inventory_item(db, audit)
    elif audit.entity_type == "location":
        await _revert_location(db, audit)
    else:
        raise ValueError("Entity type not supported for revert.")

    await create_audit_log(
        db,
        ctx,
        action="revert",
        entity_type=audit.entity_type,
        entity_id=audit.entity_id,
        before_state=audit.after_state,
        after_state=audit.before_state,
    )


async def _revert_inventory_item(db: AsyncSession, audit: AuditLog) -> None:
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == audit.entity_id))
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError("Inventory item not found.")
    for field, value in audit.before_state.items():
        if field in {"id", "tenant_id", "created_at", "updated_at"}:
            continue
        setattr(item, field, value)
    await db.flush()


async def _revert_location(db: AsyncSession, audit: AuditLog) -> None:
    result = await db.execute(select(Location).where(Location.id == audit.entity_id))
    location = result.scalar_one_or_none()
    if not location:
        raise ValueError("Location not found.")
    for field, value in audit.before_state.items():
        if field in {"id", "tenant_id", "created_at"}:
            continue
        setattr(location, field, value)
    await db.flush()
