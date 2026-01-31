from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.stores.models import Store, StoreSyncState


DEFAULT_DAILY_LIMITS: dict[str, int] = {
    "bricklink": 5000,
    "brickowl": 5000,
    "brikick": 10000,
    "shopify": 20000,
    "ebay": 5000,
    "etsy": 5000,
    "local": 100000,
}


class StoreRateLimitTracker:
    def __init__(self, db: AsyncSession, store: Store) -> None:
        self.db = db
        self.store = store

    async def can_request(self, source: str) -> bool:
        state = await self._get_state(source)
        return state["remaining"] > 0

    async def record_request(self, source: str) -> None:
        state = await self._get_state(source)
        state["remaining"] = max(0, state["remaining"] - 1)
        await self._persist_state(source, state)

    async def get_remaining(self, source: str) -> int:
        state = await self._get_state(source)
        return state["remaining"]

    async def _get_state(self, source: str) -> dict:
        sync_state = await self._ensure_sync_state()
        state = dict(sync_state.rate_limit_state or {})
        entry = state.get(source)
        now = datetime.now(timezone.utc)
        if entry:
            reset_at = datetime.fromisoformat(entry["reset_at"])
            if reset_at <= now:
                entry = None
        if not entry:
            limit = DEFAULT_DAILY_LIMITS.get(source, 5000)
            entry = {
                "limit": limit,
                "remaining": limit,
                "reset_at": (now + timedelta(days=1)).isoformat(),
            }
            state[source] = entry
            sync_state.rate_limit_state = state
            await self.db.flush()
        return entry

    async def _persist_state(self, source: str, entry: dict) -> None:
        sync_state = await self._ensure_sync_state()
        state = dict(sync_state.rate_limit_state or {})
        state[source] = entry
        sync_state.rate_limit_state = state
        await self.db.flush()

    async def _ensure_sync_state(self) -> StoreSyncState:
        result = await self.db.execute(
            select(StoreSyncState).where(StoreSyncState.store_id == self.store.id)
        )
        sync_state = result.scalar_one_or_none()
        if sync_state:
            return sync_state
        sync_state = StoreSyncState(store_id=self.store.id)
        self.db.add(sync_state)
        await self.db.flush()
        return sync_state
