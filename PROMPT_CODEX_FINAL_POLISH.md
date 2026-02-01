# Brikonnect — Final Polish & Production Ready

> **Para o Agente Codex:** Este é o passo final antes de deploy em produção.

---

## Estado Actual

✅ M1-M6 implementados (Auth, Inventory, Orders, Picker, Audit, Sync)
✅ Billing, Catalog, Brickognize, Email, Shipping implementados
✅ 29+ testes a passar

## Objectivo

Preparar o código para **produção**:
1. Correr todos os testes e corrigir falhas
2. Criar ficheiros de produção em falta
3. Polish final do frontend
4. Documentação

---

## TAREFA 1: Validar Testes

```bash
cd apps/api
pip install -r requirements-dev.txt
pytest -v --tb=short
```

Se houver testes a falhar, corrige-os.

**Resultado esperado:** Todos os testes passam.

---

## TAREFA 2: Criar Ficheiros de Produção

### 2.1 Docker Compose Produção

Criar `docker-compose.prod.yml` na raiz:

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v3.0
    container_name: brikonnect_traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=brikonnect_network"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL:-admin@brikonnect.com}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--log.level=WARN"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "traefik_certs:/letsencrypt"
    networks:
      - brikonnect_network

  db:
    image: postgres:16-alpine
    container_name: brikonnect_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-brikonnect}
      POSTGRES_USER: ${POSTGRES_USER:-brikonnect}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-brikonnect}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - brikonnect_network

  redis:
    image: redis:7-alpine
    container_name: brikonnect_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - brikonnect_network

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile.prod
    container_name: brikonnect_api
    restart: unless-stopped
    env_file:
      - ./.env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-brikonnect}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB:-brikonnect}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - brikonnect_network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.brikonnect.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=8000"
      - "traefik.http.routers.api-tenant.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api-tenant.entrypoints=websecure"
      - "traefik.http.routers.api-tenant.tls.certresolver=letsencrypt"
      - "traefik.http.routers.api-tenant.service=api"

  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile.prod
    container_name: brikonnect_worker
    restart: unless-stopped
    command: python -m arq app.jobs.worker.WorkerSettings
    env_file:
      - ./.env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-brikonnect}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB:-brikonnect}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - brikonnect_network

  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile.prod
      args:
        - VITE_API_URL=https://api.brikonnect.com
    container_name: brikonnect_web
    restart: unless-stopped
    networks:
      - brikonnect_network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`) && !PathPrefix(`/api`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=80"

networks:
  brikonnect_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  traefik_certs:
```

### 2.2 Dockerfile API (Produção)

Criar `apps/api/Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
```

### 2.3 Dockerfile Web (Produção)

Criar `apps/web/Dockerfile.prod`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/

RUN pnpm install --frozen-lockfile

COPY apps/web/ ./apps/web/

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN pnpm --filter web build

FROM nginx:alpine

COPY --from=builder /app/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2.4 Nginx Config

Criar `apps/web/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

### 2.5 GitHub Actions CI/CD

Criar/atualizar `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [main, implementation-review]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: apps/api/requirements-dev.txt

      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements-dev.txt

      - name: Lint
        run: |
          cd apps/api
          ruff check . --exit-zero

      - name: Test
        run: |
          cd apps/api
          pytest -v --tb=short
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret
          JWT_SECRET_KEY: test-jwt-secret
          ENCRYPTION_KEY: test-encryption-1234

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build API
        run: docker build -t brikonnect-api -f apps/api/Dockerfile.prod apps/api

      - name: Build Web
        run: docker build -t brikonnect-web -f apps/web/Dockerfile.prod . --build-arg VITE_API_URL=https://api.brikonnect.com
```

---

## TAREFA 3: Polish Frontend

### 3.1 Verificar ThemeToggle funciona

O ficheiro `apps/web/src/components/ThemeToggle.tsx` deve:
- Guardar preferência em localStorage
- Aplicar classe `dark` ao `<html>`
- Incluir no Layout header

Verificar e corrigir se necessário.

### 3.2 Verificar ErrorBoundary

O `ErrorBoundary.tsx` deve envolver a app em `main.tsx` ou `router.tsx`.

### 3.3 Verificar Loading States

Todas as páginas devem ter loading skeletons enquanto dados carregam.

### 3.4 Verificar Mobile Responsive

- Sidebar deve colapsar em mobile
- Tabelas devem ter scroll horizontal
- Forms devem ser full-width em mobile

---

## TAREFA 4: Actualizar README

Actualizar `README.md` na raiz com:

```markdown
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
```

---

## TAREFA 5: Verificar .env.example

Garantir que `.env.example` tem todas as variáveis:

```bash
# App
BRIKONNECT_ENV=dev
BRIKONNECT_DEBUG=1

# Database
POSTGRES_DB=brikonnect
POSTGRES_USER=brikonnect
POSTGRES_PASSWORD=brikonnect
DATABASE_URL=postgresql+asyncpg://brikonnect:brikonnect@localhost:5432/brikonnect

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=change-me-in-production
JWT_SECRET_KEY=change-me-in-production
ENCRYPTION_KEY=change-me-encryption

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Tenant
DEFAULT_TENANT_SLUG=demo
ENFORCE_TENANT_HOST=false

# Session
SESSION_COOKIE_NAME=brikonnect_session
SESSION_TTL_SECONDS=1209600

# External APIs (optional for dev)
REBRICKABLE_API_KEY=
BRICKLINK_CONSUMER_KEY=
BRICKLINK_CONSUMER_SECRET=
BRICKLINK_TOKEN=
BRICKLINK_TOKEN_SECRET=
BRICKOWL_API_KEY=
BRICKOGNIZE_API_KEY=

# Stripe (test keys for dev)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# PayPal (sandbox for dev)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=sandbox

# Email (optional for dev)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@brikonnect.com

# Monitoring (optional)
SENTRY_DSN=
LOG_LEVEL=DEBUG
```

---

## TAREFA 6: Commits

Faz commits separados para cada tarefa:

1. `fix: resolve any failing tests`
2. `feat: add production Docker files`
3. `feat: add CI/CD pipeline`
4. `chore: update README and .env.example`
5. `feat: polish frontend (theme, errors, loading)`

---

## Checklist Final

Antes de terminar, verifica:

- [ ] `pytest -v` — todos os testes passam
- [ ] `docker-compose.prod.yml` existe e é válido
- [ ] `apps/api/Dockerfile.prod` existe
- [ ] `apps/web/Dockerfile.prod` existe
- [ ] `apps/web/nginx.conf` existe
- [ ] `.github/workflows/ci.yml` está actualizado
- [ ] `README.md` está actualizado
- [ ] `.env.example` tem todas as variáveis
- [ ] ThemeToggle funciona (dark/light)
- [ ] ErrorBoundary está no lugar
- [ ] Loading skeletons nas páginas principais

---

## Comandos de Verificação

```bash
# Testes
cd apps/api && pytest -v

# Validar YAML
python -c "import yaml; yaml.safe_load(open('docker-compose.prod.yml'))"

# Lint
cd apps/api && ruff check .

# Build test (local)
docker build -t test-api -f apps/api/Dockerfile.prod apps/api
docker build -t test-web -f apps/web/Dockerfile.prod . --build-arg VITE_API_URL=http://localhost:8000
```

Quando tudo estiver completo, faz push:

```bash
git add -A
git push
```
