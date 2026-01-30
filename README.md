# Brikonnect — Production Scaffold (FastAPI + Postgres + Docker)

This repository is a **production-oriented scaffold** for Brikonnect:
- **Backend:** FastAPI (async) + SQLAlchemy 2.0 + Alembic + Postgres
- **Auth:** session-cookie (UI compatibility) + optional bearer token
- **API:** versioned under `/api/v1/*`
- **Operational basics:** structured logging, health checks, config via env, CORS, migrations, CI

> This scaffold is intentionally minimal in business logic but **complete in structure** so you can implement modules incrementally without refactoring the foundation.

---

## Quick start (Docker)

1) Copy env file:

```bash
cp .env.example .env
```

2) Start services:

```bash
docker compose up --build
```

3) Apply database migrations:

```bash
docker compose exec api alembic upgrade head
```

4) Open:
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## Local dev (no Docker)

Requirements: Python 3.11+, Postgres 14+

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env
alembic upgrade head
uvicorn app.main:app --reload
```

---

## API layout

- `/api/v1/auth/*` — login/session, token (optional)
- `/api/v1/tenants/*` — tenant bootstrap/settings
- `/api/v1/inventory/*` — inventory core (stub)
- `/api/v1/orders/*` — order core (stub)
- `/api/v1/picker/*` — picking flows (stub)
- `/api/v1/billing/*` — billing (stub)
- `/api/v1/notifications/*` — notifications (stub)
- `/api/v1/definitions/*` — enums/codes (stub)

> Endpoints are organized by module and routed through a single `api_router`.

---

## Production notes

- Use a real secret for `BRIKONNECT_SECRET_KEY`.
- Use TLS termination in front of the API (nginx/traefik) and set cookie flags accordingly.
- Consider background jobs (Celery/RQ/Arq) for long-running tasks (price sync, image fetch, BOID-like resolution, etc.).

---

## What to implement next (recommended order)

1) Auth + RBAC enforcement
2) Tenants + shops/stores model
3) Inventory model (lots, condition, qty, price, location)
4) Orders model (lines, status, shipments, invoices)
5) Integrations (marketplaces/shipping/payment) as adapters
6) Event/metrics tracking (for ranking and SLA)

