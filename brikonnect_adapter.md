# Brikonnect Demo → Brikonnect backend scaffolding (practical wiring plan)

This note compiles what is now *actionable* for making the Vue demo UI functional against **your** backend.

## 1) Minimum endpoints to get the SPA past login and into the app shell

### Auth
- `POST /api/v1/users/login/`  
  UI expects a successful response + cookie-based session.
- `GET /api/v1/users/user/`  
  UI uses this to validate session and fetch role/permission context.

### Tenant bootstrap
- `POST /api/v1/tenant/tenant/`  
  (demo uses this during bootstrap; in Brikonnect it likely resolves subdomain/tenant context)
- `GET /api/v1/tenant/tenant/detail/`  
  Must return tenant settings object. A full sample is present in HAR and implemented in the mock.

## 2) Minimum endpoints for the most-used screens (per HAR frequency)

- `GET /api/v1/integrations/integration/` (integrations registry + dynamic provider appFiles)
- `POST /api/v1/inventory/pricing/` and `GET /api/v1/inventory/pricing/`
- `GET /api/v1/inventory/problems/`
- `PATCH /api/v1/picker/settings/default/`
- `GET /api/v1/notifications/notifications/`
- `GET /api/v1/search/search/` (search results for parts/sets/minifigs)

## 3) HTML preview endpoints (content-type matters)
Observed as `text/html`:
- `POST /api/v1/orders/receipt-settings/preview/`
- `POST /api/v1/orders/notification-template/{id}/preview/`

If you implement these in FastAPI, return `HTMLResponse` not JSON.

## 4) What “/v1/API” likely was in the original codebase
Given the observed patterns:
- Vue2 + VueRouter + Vuex + Webpack code-splitting.
- Calls are consistently under `/api/v1/.../` with trailing slashes.
The “/v1/API” you mentioned is almost certainly an **internal frontend folder** (client wrappers) that maps to `/api/v1/` routes,
not a server directory.

## 5) How to use the generated artifacts
- `brikonnect_mock_backend/openapi.yaml`: base contract you can extend.
- `brikonnect_mock_backend/main.py`: a working mock server that returns captured examples.

Suggested workflow:
1) Run the mock backend and point your local UI at it.
2) Identify which endpoints the UI still calls that return stub payloads.
3) Implement those endpoints properly in your Brikonnect backend (FastAPI + Postgres).
4) Replace mock examples with real schemas in `openapi.yaml` as you harden modules.

