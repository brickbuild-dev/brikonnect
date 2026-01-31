from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.registry import get_inventory_adapter
from app.integrations.types import AdapterInventoryItem
from app.modules.audit.service import AuditContext, create_audit_log, serialize_model
from app.modules.inventory.models import InventoryExternalId, InventoryItem
from app.modules.stores.models import Store, StoreSyncState
from app.modules.stores.rate_limit import StoreRateLimitTracker
from app.modules.sync.models import SyncPlanItem, SyncRun
from app.modules.sync.schemas import SyncPreviewRequest


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def list_runs(db: AsyncSession, tenant_id) -> list[SyncRun]:
    result = await db.execute(
        select(SyncRun).where(SyncRun.tenant_id == tenant_id).order_by(SyncRun.created_at.desc())
    )
    return list(result.scalars().all())


async def get_run(db: AsyncSession, tenant_id, run_id) -> SyncRun | None:
    result = await db.execute(
        select(SyncRun).where(SyncRun.tenant_id == tenant_id, SyncRun.id == run_id)
    )
    return result.scalar_one_or_none()


async def list_plan_items(db: AsyncSession, run: SyncRun) -> list[SyncPlanItem]:
    result = await db.execute(
        select(SyncPlanItem).where(SyncPlanItem.sync_run_id == run.id).order_by(SyncPlanItem.id)
    )
    return list(result.scalars().all())


async def create_preview(
    db: AsyncSession, tenant_id, user_id, payload: SyncPreviewRequest
) -> SyncRun:
    if payload.direction not in {"SOURCE_TO_TARGET"}:
        raise ValueError("Only SOURCE_TO_TARGET is supported right now.")

    source_store = await _get_store(db, tenant_id, payload.source_store_id)
    target_store = await _get_store(db, tenant_id, payload.target_store_id)
    if source_store.id == target_store.id:
        raise ValueError("Source and target stores must differ.")

    run = SyncRun(
        tenant_id=tenant_id,
        source_store_id=source_store.id,
        target_store_id=target_store.id,
        mode="PREVIEW",
        direction=payload.direction,
        status="PENDING",
        created_by=user_id,
        started_at=_now(),
    )
    db.add(run)
    await db.flush()

    run.status = "FETCHING"
    await db.flush()
    source_adapter = get_inventory_adapter(db, source_store)
    target_adapter = get_inventory_adapter(db, target_store)
    source_items = await source_adapter.fetch_inventory()
    target_items = await target_adapter.fetch_inventory()

    run.status = "COMPARING"
    await db.flush()
    plan_items, summary = await _build_plan(
        db,
        tenant_id,
        source_items,
        target_items,
        allow_large_removals=payload.allow_large_removals,
    )
    for item in plan_items:
        item.sync_run_id = run.id
        db.add(item)

    run.plan_summary = summary
    run.status = "PREVIEW_READY"
    await db.flush()
    return run


async def approve_run(
    db: AsyncSession,
    run: SyncRun,
    user_id,
    audit_ctx: AuditContext,
    checkpoint_every: int = 25,
) -> SyncRun:
    if run.status not in {"PREVIEW_READY", "FAILED"}:
        raise ValueError("Sync run cannot be approved in its current state.")

    run.mode = "APPLY"
    run.status = "APPLYING"
    run.approved_by = user_id
    run.approved_at = _now()
    await db.flush()

    target_store = await _get_store(db, run.tenant_id, run.target_store_id)
    adapter = get_inventory_adapter(db, target_store)
    rate_limit = StoreRateLimitTracker(db, target_store)

    plan_items = await list_plan_items(db, run)
    processed = 0
    for plan_item in plan_items:
        if plan_item.status != "PENDING":
            continue
        if plan_item.action == "SKIP":
            plan_item.status = "SKIPPED"
            plan_item.applied_at = _now()
            continue

        if not await rate_limit.can_request(target_store.channel):
            run.status = "FAILED"
            run.error_message = "Rate limit exceeded"
            break
        await rate_limit.record_request(target_store.channel)

        try:
            adapter_item = AdapterInventoryItem.model_validate(
                plan_item.after_state or plan_item.before_state
            )
            if plan_item.target_external_id:
                adapter_item = adapter_item.model_copy(
                    update={"external_id": plan_item.target_external_id}
                )
            adapter_result = await adapter.apply_change(plan_item.action, adapter_item)
            if plan_item.action == "ADD":
                plan_item.target_external_id = adapter_result.external_id
            await _apply_local_inventory(
                db,
                audit_ctx,
                run.tenant_id,
                target_store.id,
                plan_item,
                adapter_result,
            )
            plan_item.status = "APPLIED"
            plan_item.applied_at = _now()
        except Exception as exc:  # pragma: no cover - defensive
            plan_item.status = "FAILED"
            plan_item.error_message = str(exc)
            run.status = "FAILED"
            run.error_message = str(exc)
            break

        processed += 1
        if processed % checkpoint_every == 0:
            await db.flush()

    if run.status != "FAILED":
        run.status = "COMPLETED"
        run.completed_at = _now()
        await _touch_sync_state(db, target_store.id)
    await db.flush()
    return run


async def cancel_run(db: AsyncSession, run: SyncRun) -> SyncRun:
    if run.status in {"COMPLETED", "FAILED"}:
        return run
    run.status = "CANCELLED"
    await db.flush()
    return run


async def _get_store(db: AsyncSession, tenant_id, store_id) -> Store:
    result = await db.execute(
        select(Store).where(Store.tenant_id == tenant_id, Store.id == store_id)
    )
    store = result.scalar_one_or_none()
    if not store:
        raise ValueError("Store not found")
    return store


def _diff_item(source: AdapterInventoryItem, target: AdapterInventoryItem) -> list[dict]:
    changes = []
    if source.qty_available != target.qty_available:
        changes.append(
            {
                "field": "qty_available",
                "old": _json_value(target.qty_available),
                "new": _json_value(source.qty_available),
            }
        )
    if source.unit_price != target.unit_price:
        changes.append(
            {
                "field": "unit_price",
                "old": _json_value(target.unit_price),
                "new": _json_value(source.unit_price),
            }
        )
    if (source.remarks or "") != (target.remarks or ""):
        changes.append({"field": "remarks", "old": target.remarks, "new": source.remarks})
    return changes


async def _build_plan(
    db: AsyncSession,
    tenant_id,
    source_items: list[AdapterInventoryItem],
    target_items: list[AdapterInventoryItem],
    allow_large_removals: bool,
) -> tuple[list[SyncPlanItem], dict]:
    source_map = {item.key(): item for item in source_items}
    target_map = {item.key(): item for item in target_items}

    existing_items = await db.execute(
        select(InventoryItem).where(InventoryItem.tenant_id == tenant_id)
    )
    existing_by_key = {item.key(): item for item in existing_items.scalars().all()}

    plan_items: list[SyncPlanItem] = []
    summary = {"add": 0, "update": 0, "remove": 0, "unmatched": 0, "skip": 0}

    target_count = max(len(target_map), 1)
    remove_candidates: list[SyncPlanItem] = []

    all_keys = set(source_map.keys()) | set(target_map.keys())
    for key in all_keys:
        source_item = source_map.get(key)
        target_item = target_map.get(key)

        if source_item and not target_item:
            plan_items.append(
                SyncPlanItem(
                    action="ADD",
                    inventory_item_id=existing_by_key.get(key).id if existing_by_key.get(key) else None,
                    source_external_id=source_item.external_id,
                    before_state=None,
                    after_state=source_item.to_state(),
                    changes=[{"field": "full", "old": None, "new": source_item.to_state()}],
                )
            )
            summary["add"] += 1
        elif target_item and not source_item:
            item = SyncPlanItem(
                action="REMOVE",
                inventory_item_id=existing_by_key.get(key).id if existing_by_key.get(key) else None,
                target_external_id=target_item.external_id,
                before_state=target_item.to_state(),
                after_state=None,
                changes=[{"field": "full", "old": target_item.to_state(), "new": None}],
            )
            remove_candidates.append(item)
            summary["remove"] += 1
        elif source_item and target_item:
            changes = _diff_item(source_item, target_item)
            if changes:
                plan_items.append(
                    SyncPlanItem(
                        action="UPDATE",
                        inventory_item_id=existing_by_key.get(key).id if existing_by_key.get(key) else None,
                        source_external_id=source_item.external_id,
                        target_external_id=target_item.external_id,
                        before_state=target_item.to_state(),
                        after_state=source_item.to_state(),
                        changes=changes,
                    )
                )
                summary["update"] += 1
            else:
                plan_items.append(
                    SyncPlanItem(
                        action="SKIP",
                        skip_reason="NO_CHANGE",
                        inventory_item_id=existing_by_key.get(key).id if existing_by_key.get(key) else None,
                        source_external_id=source_item.external_id,
                        target_external_id=target_item.external_id,
                        before_state=target_item.to_state(),
                        after_state=source_item.to_state(),
                        changes=[],
                        status="SKIPPED",
                    )
                )
                summary["skip"] += 1
        else:
            summary["unmatched"] += 1

    if remove_candidates and not allow_large_removals:
        removal_ratio = len(remove_candidates) / target_count
        if removal_ratio > 0.1:
            for item in remove_candidates:
                item.action = "SKIP"
                item.skip_reason = "REMOVE_THRESHOLD"
                item.status = "SKIPPED"
                summary["remove"] -= 1
                summary["skip"] += 1
        else:
            plan_items.extend(remove_candidates)
    else:
        plan_items.extend(remove_candidates)

    return plan_items, summary


async def _apply_local_inventory(
    db: AsyncSession,
    audit_ctx: AuditContext,
    tenant_id,
    store_id,
    plan_item: SyncPlanItem,
    adapter_item: AdapterInventoryItem,
) -> None:
    key = adapter_item.key()
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.item_type == key[0],
            InventoryItem.item_no == key[1],
            InventoryItem.color_id == key[2],
            InventoryItem.condition == key[3],
        )
    )
    inventory_item = result.scalar_one_or_none()

    before_state = serialize_model(inventory_item) if inventory_item else None

    if plan_item.action == "REMOVE":
        if inventory_item:
            inventory_item.qty_available = 0
    else:
        if not inventory_item:
            inventory_item = InventoryItem(
                tenant_id=tenant_id,
                item_type=adapter_item.item_type,
                item_no=adapter_item.item_no,
                color_id=adapter_item.color_id,
                condition=adapter_item.condition,
                qty_available=adapter_item.qty_available,
                unit_price=_coerce_decimal(adapter_item.unit_price),
                remarks=adapter_item.remarks,
            )
            db.add(inventory_item)
            await db.flush()
        else:
            inventory_item.qty_available = adapter_item.qty_available
            inventory_item.unit_price = _coerce_decimal(adapter_item.unit_price)
            inventory_item.remarks = adapter_item.remarks
    if inventory_item:
        plan_item.inventory_item_id = inventory_item.id

    if inventory_item:
        await _upsert_external_id(
            db,
            tenant_id,
            inventory_item,
            store_id,
            plan_item.target_external_id or adapter_item.external_id,
        )

    after_state = serialize_model(inventory_item) if inventory_item else None
    await create_audit_log(
        db,
        audit_ctx,
        action="sync_apply",
        entity_type="inventory_item",
        entity_id=inventory_item.id if inventory_item else None,
        before_state=before_state,
        after_state=after_state,
    )


async def _upsert_external_id(
    db: AsyncSession,
    tenant_id,
    inventory_item: InventoryItem,
    store_id,
    external_id: str | None,
) -> None:
    if not external_id:
        return
    result = await db.execute(
        select(InventoryExternalId).where(
            InventoryExternalId.inventory_item_id == inventory_item.id,
            InventoryExternalId.store_id == store_id,
        )
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        mapping.external_inventory_id = external_id
        mapping.last_synced_at = _now()
    else:
        mapping = InventoryExternalId(
            tenant_id=tenant_id,
            inventory_item_id=inventory_item.id,
            store_id=store_id,
            external_inventory_id=external_id,
            last_synced_at=_now(),
        )
        db.add(mapping)
    await db.flush()


async def _touch_sync_state(db: AsyncSession, store_id) -> None:
    result = await db.execute(
        select(StoreSyncState).where(StoreSyncState.store_id == store_id)
    )
    sync_state = result.scalar_one_or_none()
    if not sync_state:
        sync_state = StoreSyncState(store_id=store_id)
        db.add(sync_state)
    sync_state.last_inventory_sync = _now()
    await db.flush()


def _coerce_decimal(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    return value
