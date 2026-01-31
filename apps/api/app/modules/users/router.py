from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import get_db
from app.modules.rbac.deps import require_permissions
from app.modules.rbac.schemas import AssignRoleRequest
from app.modules.users.schemas import UserCreate, UserOut, UserUpdate
from app.modules.users.service import (
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    set_user_roles,
    update_user,
)

router = APIRouter()


@router.get("/", response_model=list[UserOut])
async def list_all(
    current_user=Depends(require_permissions(["users:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_users(db, current_user.tenant_id)


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: UserCreate,
    current_user=Depends(require_permissions(["users:write"])),
    db: AsyncSession = Depends(get_db),
):
    hashed = hash_password(payload.password)
    user = await create_user(db, current_user.tenant_id, payload, hashed)
    await db.commit()
    return user


@router.get("/{user_id}", response_model=UserOut)
async def get(
    user_id: UUID,
    current_user=Depends(require_permissions(["users:read"])),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, current_user.tenant_id, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update(
    user_id: UUID,
    payload: UserUpdate,
    current_user=Depends(require_permissions(["users:write"])),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, current_user.tenant_id, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.password is not None:
        payload = payload.model_copy(update={"password": hash_password(payload.password)})
    user = await update_user(db, user, payload)
    await db.commit()
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    user_id: UUID,
    current_user=Depends(require_permissions(["users:write"])),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, current_user.tenant_id, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await delete_user(db, user)
    await db.commit()
    return None


@router.post("/{user_id}/roles", response_model=list[str])
async def assign_roles(
    user_id: UUID,
    payload: AssignRoleRequest,
    current_user=Depends(require_permissions(["roles:manage"])),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, current_user.tenant_id, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    roles = await set_user_roles(db, current_user.tenant_id, user.id, payload.role_ids)
    await db.commit()
    return [role.name for role in roles]
