from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    permissions: list[str] | None = None


class RoleOut(RoleBase):
    id: UUID
    tenant_id: UUID
    is_system: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list, min_length=1)
