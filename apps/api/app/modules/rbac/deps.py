from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.deps import get_current_user
from app.modules.rbac import service as rbac_service


async def get_current_permissions(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    return await rbac_service.get_user_permissions(db, user.tenant_id, user.id)


def require_permissions(required: list[str]):
    async def _dep(
        user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        permissions = await rbac_service.get_user_permissions(db, user.tenant_id, user.id)
        if not set(required).issubset(set(permissions)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _dep
