from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth import router as auth_router
from app.modules.rbac import router as rbac_router
from app.modules.tenants import router as tenants_router
from app.modules.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants_router.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users_router.router, prefix="/users", tags=["users"])
api_router.include_router(rbac_router.router, prefix="/roles", tags=["rbac"])

