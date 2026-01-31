from __future__ import annotations

# Permissions list follows PROMPT_BRIKONNECT_V2.md
PERMISSIONS: list[str] = [
    # Inventory
    "inventory:read",
    "inventory:write",
    "inventory:delete",
    "inventory:import",
    "inventory:export",
    # Orders
    "orders:read",
    "orders:write",
    "orders:status_update",
    "orders:cancel",
    "orders:refund",
    # Picker
    "picker:read",
    "picker:create_session",
    "picker:pick",
    "picker:manage_sessions",
    # Stores
    "stores:read",
    "stores:write",
    "stores:credentials",
    # Sync
    "sync:read",
    "sync:preview",
    "sync:apply",
    # Users/RBAC
    "users:read",
    "users:write",
    "users:invite",
    "roles:manage",
    # Audit
    "audit:read",
    # Settings
    "settings:read",
    "settings:write",
    "billing:manage",
    # API/Webhooks
    "api_keys:manage",
    "webhooks:manage",
]


ROLE_PERMISSIONS: dict[str, list[str]] = {
    "owner": PERMISSIONS.copy(),
    "admin": [p for p in PERMISSIONS if p != "billing:manage"],
    "staff": [
        # Inventory
        "inventory:read",
        "inventory:write",
        "inventory:delete",
        "inventory:import",
        "inventory:export",
        # Orders
        "orders:read",
        "orders:write",
        "orders:status_update",
        "orders:cancel",
        "orders:refund",
        # Picker
        "picker:read",
        "picker:create_session",
        "picker:pick",
        "picker:manage_sessions",
        # Stores (read-only)
        "stores:read",
        # Sync (preview only)
        "sync:read",
        "sync:preview",
        # Audit
        "audit:read",
        # Settings (read)
        "settings:read",
    ],
    "picker": [
        "inventory:read",
        "orders:read",
        "orders:status_update",
        "picker:read",
        "picker:create_session",
        "picker:pick",
        "picker:manage_sessions",
    ],
    "readonly": [
        "inventory:read",
        "orders:read",
        "stores:read",
        "picker:read",
    ],
}
