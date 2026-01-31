from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.rbac.deps import require_permissions
from app.modules.rbac.schemas import RoleCreate, RoleOut, RoleUpdate
from app.modules.rbac.service import create_role, delete_role, get_role_by_id, list_roles, update_role

router = APIRouter()


@router.get("/", response_model=list[RoleOut])
async def list_all(
    current_user=Depends(require_permissions(["roles:manage"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_roles(db, current_user.tenant_id)


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: RoleCreate,
    current_user=Depends(require_permissions(["roles:manage"])),
    db: AsyncSession = Depends(get_db),
):
    role = await create_role(db, current_user.tenant_id, payload.name, payload.permissions)
    await db.commit()
    return role


@router.patch("/{role_id}", response_model=RoleOut)
async def update(
    role_id: UUID,
    payload: RoleUpdate,
    current_user=Depends(require_permissions(["roles:manage"])),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role_by_id(db, current_user.tenant_id, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role = await update_role(db, role, payload.name, payload.permissions)
    await db.commit()
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    role_id: UUID,
    current_user=Depends(require_permissions(["roles:manage"])),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role_by_id(db, current_user.tenant_id, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    await delete_role(db, role)
    await db.commit()
    return None
