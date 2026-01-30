from __future__ import annotations

from pydantic import BaseModel

class TenantCreate(BaseModel):
    slug: str
    name: str

class TenantOut(BaseModel):
    id: int
    slug: str
    name: str
