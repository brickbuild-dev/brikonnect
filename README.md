# Brikonnect

SaaS platform for LEGO sellers.

## Features

- Multi-channel inventory management (BrickLink, BrickOwl, Brikick)
- Order management with status workflow
- Picking system with optimized routes
- Cross-platform inventory sync
- Billing (GMV-based)
- Visual part recognition (Brickognize)
- Shipping label generation

## Quick Start

### Development

```bash
# Clone
git clone https://github.com/brickbuild-dev/brikonnect.git
cd brikonnect

# Start database
docker compose up -d db redis

# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload

# Frontend (another terminal)
cd apps/web
pnpm install && pnpm dev
```

### Production

See `PRODUCTION_CHECKLIST.md` for full deployment guide.

```bash
cp .env.example .env
# Edit .env with production values
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## Architecture

```
apps/
├── api/          # FastAPI backend
├── web/          # React frontend
└── extension/    # Chrome extension

packages/
├── sdk/          # TypeScript API client
└── ui/           # Shared components
```

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis
- **Frontend:** React 18, TypeScript, Vite, TanStack Query
- **Infrastructure:** Docker, Traefik, GitHub Actions

## API Documentation

Available at `/docs` when running the API.

## License

Proprietary - All rights reserved.

