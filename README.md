# Brikonnect — Platform Monorepo

Brikonnect is a SaaS platform for LEGO sellers, built as a monorepo:
- **Backend:** FastAPI (async) + SQLAlchemy 2.0 + Alembic + Postgres
- **Frontend:** React 18 + TypeScript + Vite + TanStack Query/Router
- **Monorepo:** Turborepo + pnpm

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
- Web app: http://localhost:3000

---

## Local dev (no Docker)

Requirements: Python 3.11+, Postgres 14+

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd apps/web
pnpm install
pnpm dev
```

---

## API layout

Core modules are organized under `apps/api/app/modules` and routed via `/api/v1/*`.

> Endpoints are organized by module and routed through a single `api_router`.

---

## Production notes

- Use real secrets for `SECRET_KEY` and `JWT_SECRET_KEY`.
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

