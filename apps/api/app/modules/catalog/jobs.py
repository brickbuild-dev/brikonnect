from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def import_bricklink_dumps(db: AsyncSession) -> int:
    return 0


async def sync_rebrickable_mappings(db: AsyncSession) -> int:
    return 0


async def refresh_stale_items(db: AsyncSession) -> int:
    return 0
