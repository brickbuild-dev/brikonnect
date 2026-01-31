from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_payload, encrypt_payload
from app.modules.stores.models import Store, StoreCredential, StoreSyncState
from app.modules.stores.schemas import StoreCreate, StoreCredentialsPayload, StoreUpdate


async def list_stores(db: AsyncSession, tenant_id) -> list[Store]:
    result = await db.execute(select(Store).where(Store.tenant_id == tenant_id))
    return list(result.scalars().all())


async def get_store(db: AsyncSession, tenant_id, store_id) -> Store | None:
    result = await db.execute(
        select(Store).where(Store.tenant_id == tenant_id, Store.id == store_id)
    )
    return result.scalar_one_or_none()


async def create_store(db: AsyncSession, tenant_id, payload: StoreCreate) -> Store:
    if payload.is_primary:
        await _clear_primary(db, tenant_id)
    store = Store(
        tenant_id=tenant_id,
        channel=payload.channel,
        name=payload.name,
        is_enabled=payload.is_enabled,
        is_primary=payload.is_primary,
        settings=payload.settings,
    )
    db.add(store)
    await db.flush()
    await ensure_sync_state(db, store.id)
    return store


async def update_store(db: AsyncSession, store: Store, payload: StoreUpdate) -> Store:
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_primary"):
        await _clear_primary(db, store.tenant_id)
    for field, value in data.items():
        setattr(store, field, value)
    await db.flush()
    return store


async def delete_store(db: AsyncSession, store: Store) -> None:
    await db.execute(delete(Store).where(Store.id == store.id))


async def set_store_credentials(
    db: AsyncSession, store: Store, payload: StoreCredentialsPayload
) -> StoreCredential:
    encrypted = encrypt_payload(payload.data)
    result = await db.execute(
        select(StoreCredential).where(StoreCredential.store_id == store.id)
    )
    credentials = result.scalar_one_or_none()
    if credentials:
        credentials.encrypted_data = encrypted
        credentials.encryption_key_id = "default"
    else:
        credentials = StoreCredential(
            store_id=store.id,
            encrypted_data=encrypted,
            encryption_key_id="default",
        )
        db.add(credentials)
    await db.flush()
    return credentials


async def get_store_credentials(db: AsyncSession, store: Store) -> dict | None:
    result = await db.execute(
        select(StoreCredential).where(StoreCredential.store_id == store.id)
    )
    credentials = result.scalar_one_or_none()
    if not credentials:
        return None
    return decrypt_payload(credentials.encrypted_data)


async def ensure_sync_state(db: AsyncSession, store_id) -> StoreSyncState:
    result = await db.execute(
        select(StoreSyncState).where(StoreSyncState.store_id == store_id)
    )
    sync_state = result.scalar_one_or_none()
    if sync_state:
        return sync_state
    sync_state = StoreSyncState(store_id=store_id)
    db.add(sync_state)
    await db.flush()
    return sync_state


async def _clear_primary(db: AsyncSession, tenant_id) -> None:
    await db.execute(
        update(Store)
        .where(Store.tenant_id == tenant_id, Store.is_primary.is_(True))
        .values(is_primary=False)
    )
