# Brikonnect — Production Checklist

> Checklist completo para deploy em produção no VPS.

---

## 1. Infraestrutura

### 1.1 VPS Setup

- [ ] **VPS provisionado** (mínimo recomendado: 4GB RAM, 2 vCPU, 80GB SSD)
- [ ] **OS instalado:** Ubuntu 22.04 LTS ou Debian 12
- [ ] **Docker instalado:**
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
  ```
- [ ] **Docker Compose instalado:**
  ```bash
  sudo apt install docker-compose-plugin
  ```
- [ ] **Firewall configurado:**
  ```bash
  sudo ufw allow 22/tcp    # SSH
  sudo ufw allow 80/tcp    # HTTP
  sudo ufw allow 443/tcp   # HTTPS
  sudo ufw enable
  ```

### 1.2 DNS

- [ ] **A Record:** `api.brikonnect.com` → IP do VPS
- [ ] **A Record:** `*.brikonnect.com` → IP do VPS (wildcard para tenants)
- [ ] **A Record:** `www.brikonnect.com` → IP do VPS (landing page)
- [ ] **TTL:** 300 segundos (5 min) para início, aumentar depois

### 1.3 SSL/TLS

- [ ] **Let's Encrypt** via Traefik (automático)
- [ ] **Wildcard certificate** configurado (ver Traefik config abaixo)

---

## 2. Secrets & Environment Variables

### 2.1 Gerar Secrets

```bash
# SECRET_KEY (64 chars)
openssl rand -hex 32

# JWT_SECRET_KEY (64 chars)
openssl rand -hex 32

# ENCRYPTION_KEY (32 chars for AES-256)
openssl rand -hex 16

# Webhook secrets
openssl rand -hex 20
```

### 2.2 Ficheiro .env (Produção)

```bash
# ===========================================
# BRIKONNECT PRODUCTION ENVIRONMENT
# ===========================================

# Environment
BRIKONNECT_ENV=production
BRIKONNECT_DEBUG=0

# Database
POSTGRES_DB=brikonnect
POSTGRES_USER=brikonnect
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>
DATABASE_URL=postgresql+asyncpg://brikonnect:<PASSWORD>@db:5432/brikonnect

# Redis
REDIS_URL=redis://redis:6379/0

# Security (GENERATE THESE!)
SECRET_KEY=<64_CHAR_HEX>
JWT_SECRET_KEY=<64_CHAR_HEX>
ENCRYPTION_KEY=<32_CHAR_HEX>

# Domain
ALLOWED_HOSTS=*.brikonnect.com,api.brikonnect.com
CORS_ORIGINS=https://*.brikonnect.com

# Session
SESSION_COOKIE_NAME=brikonnect_session
SESSION_TTL_SECONDS=1209600

# Tenant
DEFAULT_TENANT_SLUG=demo
ENFORCE_TENANT_HOST=true

# External APIs
REBRICKABLE_API_KEY=<YOUR_KEY>
BRICKLINK_CONSUMER_KEY=<YOUR_KEY>
BRICKLINK_CONSUMER_SECRET=<YOUR_SECRET>
BRICKLINK_TOKEN=<YOUR_TOKEN>
BRICKLINK_TOKEN_SECRET=<YOUR_TOKEN_SECRET>
BRICKOWL_API_KEY=<YOUR_KEY>
BRICKOGNIZE_API_KEY=<YOUR_KEY>

# Stripe
STRIPE_SECRET_KEY=sk_live_<YOUR_KEY>
STRIPE_PUBLISHABLE_KEY=pk_live_<YOUR_KEY>
STRIPE_WEBHOOK_SECRET=whsec_<YOUR_SECRET>

# PayPal
PAYPAL_CLIENT_ID=<YOUR_CLIENT_ID>
PAYPAL_CLIENT_SECRET=<YOUR_SECRET>
PAYPAL_MODE=live

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=help@brikonnect.com
SMTP_PASSWORD=<YOUR_PASSWORD>
SMTP_FROM=help@brikonnect.com
SMTP_TLS=true

# Monitoring
SENTRY_DSN=https://<KEY>@sentry.io/<PROJECT>
LOG_LEVEL=INFO

# Features
FEATURES_MULTI_TENANT=true
FEATURES_BILLING=true
FEATURES_SYNC=true
FEATURES_WEBHOOKS=true
FEATURES_PUBLIC_API=true
```

### 2.3 Security Checklist

- [ ] Todos os secrets são únicos e fortes (min 32 chars)
- [ ] `.env` não está no git (verificar `.gitignore`)
- [ ] Passwords de DB não são os defaults
- [ ] Stripe/PayPal em modo LIVE (não test/sandbox)
- [ ] SMTP credentials válidas

---

## 3. Docker Compose (Produção)

### 3.1 Criar `docker-compose.prod.yml`

```yaml
version: "3.9"

services:
  # ===========================================
  # TRAEFIK - Reverse Proxy & SSL
  # ===========================================
  traefik:
    image: traefik:v3.0
    container_name: brikonnect_traefik
    restart: unless-stopped
    command:
      # API & Dashboard
      - "--api.dashboard=true"
      - "--api.insecure=false"
      
      # Providers
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=brikonnect_network"
      
      # Entrypoints
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      
      # Let's Encrypt
      - "--certificatesresolvers.letsencrypt.acme.email=admin@brikonnect.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      
      # Logs
      - "--accesslog=true"
      - "--log.level=INFO"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "traefik_certs:/letsencrypt"
    networks:
      - brikonnect_network
    labels:
      # Dashboard (protegido por auth)
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.brikonnect.com`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dashboard.middlewares=dashboard-auth"
      - "traefik.http.middlewares.dashboard-auth.basicauth.users=admin:$$apr1$$xyz..."  # htpasswd

  # ===========================================
  # DATABASE - PostgreSQL
  # ===========================================
  db:
    image: postgres:16-alpine
    container_name: brikonnect_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups  # Para backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - brikonnect_network

  # ===========================================
  # CACHE - Redis
  # ===========================================
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

  # ===========================================
  # API - FastAPI Backend
  # ===========================================
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: brikonnect_api
    restart: unless-stopped
    env_file:
      - ./.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - brikonnect_network
    labels:
      - "traefik.enable=true"
      # API principal
      - "traefik.http.routers.api.rule=Host(`api.brikonnect.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=8000"
      # API via tenant subdomains
      - "traefik.http.routers.api-tenant.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api-tenant.entrypoints=websecure"
      - "traefik.http.routers.api-tenant.tls.certresolver=letsencrypt"
      - "traefik.http.routers.api-tenant.service=api"
      # Rate limiting
      - "traefik.http.middlewares.api-ratelimit.ratelimit.average=100"
      - "traefik.http.middlewares.api-ratelimit.ratelimit.burst=50"
      - "traefik.http.routers.api.middlewares=api-ratelimit"
      - "traefik.http.routers.api-tenant.middlewares=api-ratelimit"

  # ===========================================
  # WORKER - Background Jobs (Arq)
  # ===========================================
  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: brikonnect_worker
    restart: unless-stopped
    command: arq app.jobs.worker.WorkerSettings
    env_file:
      - ./.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - brikonnect_network

  # ===========================================
  # WEB - React Frontend
  # ===========================================
  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
      args:
        VITE_API_URL: https://api.brikonnect.com
    container_name: brikonnect_web
    restart: unless-stopped
    networks:
      - brikonnect_network
    labels:
      - "traefik.enable=true"
      # Tenant subdomains serve web app
      - "traefik.http.routers.web.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`) && !PathPrefix(`/api`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=3000"
      # Compression
      - "traefik.http.middlewares.web-compress.compress=true"
      - "traefik.http.routers.web.middlewares=web-compress"

  # ===========================================
  # SCHEDULER - Cron Jobs
  # ===========================================
  scheduler:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: brikonnect_scheduler
    restart: unless-stopped
    command: python -m app.scheduler
    env_file:
      - ./.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - brikonnect_network

networks:
  brikonnect_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  traefik_certs:
```

### 3.2 Dockerfile API (Produção)

Verificar/atualizar `apps/api/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
```

### 3.3 Dockerfile Web (Produção)

Verificar/atualizar `apps/web/Dockerfile`:

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files
COPY package.json pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source
COPY apps/web/ ./apps/web/

# Build
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN pnpm --filter web build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html

# Copy nginx config
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

### 3.4 Nginx Config para SPA

Criar `apps/web/nginx.conf`:

```nginx
server {
    listen 3000;
    server_name _;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
    
    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Health check
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

---

## 4. CI/CD Pipeline

### 4.1 GitHub Actions

Criar/atualizar `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [main, implementation-review]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ===========================================
  # TEST
  # ===========================================
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
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          cd apps/api
          ruff check .
      
      - name: Run tests
        run: |
          cd apps/api
          pytest -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci
          JWT_SECRET_KEY: test-jwt-secret-for-ci
          ENCRYPTION_KEY: test-encryption-key-1234
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./apps/api/coverage.xml
          fail_ci_if_error: false

  # ===========================================
  # BUILD & PUSH
  # ===========================================
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push API
        uses: docker/build-push-action@v5
        with:
          context: ./apps/api
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push Web
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./apps/web/Dockerfile
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/web:latest
          build-args: |
            VITE_API_URL=https://api.brikonnect.com
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ===========================================
  # DEPLOY
  # ===========================================
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/brikonnect
            
            # Pull latest images
            docker compose -f docker-compose.prod.yml pull
            
            # Run migrations
            docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
            
            # Restart services
            docker compose -f docker-compose.prod.yml up -d --remove-orphans
            
            # Cleanup old images
            docker image prune -f
            
            # Health check
            sleep 10
            curl -f https://api.brikonnect.com/health || exit 1
```

### 4.2 GitHub Secrets Necessários

Configurar em Settings → Secrets → Actions:

| Secret | Descrição |
|--------|-----------|
| `VPS_HOST` | IP ou hostname do VPS |
| `VPS_USER` | Username SSH (ex: deploy) |
| `VPS_SSH_KEY` | Private key para SSH |
| `CODECOV_TOKEN` | Token do Codecov (opcional) |

---

## 5. Backups

### 5.1 Script de Backup

Criar `scripts/backup.sh`:

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/opt/brikonnect/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="s3://brikonnect-backups"  # Optional

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Backing up database..."
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Redis backup (RDB)
echo "Backing up Redis..."
docker compose -f docker-compose.prod.yml exec -T redis \
    redis-cli BGSAVE
sleep 5
docker cp brikonnect_redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Upload to S3 (optional)
if command -v aws &> /dev/null; then
    echo "Uploading to S3..."
    aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz $S3_BUCKET/
    aws s3 cp $BACKUP_DIR/redis_$DATE.rdb $S3_BUCKET/
fi

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.rdb" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

### 5.2 Cron para Backups

```bash
# Adicionar ao crontab do VPS
# crontab -e

# Daily backup at 3 AM
0 3 * * * /opt/brikonnect/scripts/backup.sh >> /var/log/brikonnect-backup.log 2>&1
```

---

## 6. Monitoring

### 6.1 Sentry (Error Tracking)

- [ ] Criar projeto em sentry.io
- [ ] Obter DSN
- [ ] Adicionar `SENTRY_DSN` ao `.env`
- [ ] Verificar que erros aparecem no dashboard

### 6.2 Uptime Monitoring

Configurar em UptimeRobot, Pingdom, ou similar:

| Check | URL | Interval |
|-------|-----|----------|
| API Health | `https://api.brikonnect.com/health` | 1 min |
| Web App | `https://demo.brikonnect.com` | 5 min |
| Database | via API `/ready` | 5 min |

### 6.3 Logs

```bash
# Ver logs em tempo real
docker compose -f docker-compose.prod.yml logs -f

# Logs específicos
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f worker
docker compose -f docker-compose.prod.yml logs -f traefik
```

---

## 7. Security Hardening

### 7.1 VPS

- [ ] SSH key-only auth (disable password)
- [ ] Fail2ban instalado
- [ ] Automatic security updates
- [ ] Non-root user para deploy

```bash
# Disable root SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Auto updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 7.2 Application

- [ ] CORS restrito a domínios permitidos
- [ ] Rate limiting activo
- [ ] CSRF protection em formulários
- [ ] Helmet headers (via Traefik)
- [ ] SQL injection prevention (SQLAlchemy)
- [ ] XSS prevention (React escapes by default)

### 7.3 Traefik Security Headers

Adicionar ao docker-compose:

```yaml
labels:
  - "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
  - "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true"
  - "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true"
  - "traefik.http.middlewares.security-headers.headers.frameDeny=true"
  - "traefik.http.middlewares.security-headers.headers.browserXssFilter=true"
```

---

## 8. Pre-Launch Checklist

### 8.1 Funcional

- [ ] Login funciona (cookie + token)
- [ ] Criar tenant funciona
- [ ] CRUD inventory funciona
- [ ] CRUD orders funciona
- [ ] Picking flow funciona
- [ ] Sync preview + apply funciona
- [ ] Billing calcula correctamente
- [ ] Pagamento Stripe funciona
- [ ] Pagamento PayPal funciona
- [ ] Emails são enviados
- [ ] Webhooks disparam

### 8.2 Performance

- [ ] Tempo de resposta API < 200ms (p95)
- [ ] Página carrega < 3s
- [ ] Sem memory leaks no worker
- [ ] DB queries optimizadas (sem N+1)

### 8.3 Legal/Compliance

- [ ] Terms of Service página
- [ ] Privacy Policy página
- [ ] GDPR compliance (EU)
- [ ] Cookie consent banner
- [ ] Data retention policy

---

## 9. Deploy Commands

### 9.1 Primeiro Deploy

```bash
# No VPS
cd /opt
git clone https://github.com/brickbuild-dev/brikonnect.git
cd brikonnect

# Configurar environment
cp .env.example .env
nano .env  # Editar com valores de produção

# Build e start
docker compose -f docker-compose.prod.yml up -d --build

# Migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Seed inicial (tenant demo)
docker compose -f docker-compose.prod.yml exec api python -m app.seed

# Verificar
curl https://api.brikonnect.com/health
```

### 9.2 Updates

```bash
cd /opt/brikonnect

# Pull changes
git pull origin main

# Rebuild e restart
docker compose -f docker-compose.prod.yml up -d --build

# Migrations (se houver novas)
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 9.3 Rollback

```bash
# Ver versões anteriores
docker images | grep brikonnect

# Rollback para versão anterior
docker compose -f docker-compose.prod.yml down
git checkout <previous-commit>
docker compose -f docker-compose.prod.yml up -d --build

# Rollback migration
docker compose -f docker-compose.prod.yml exec api alembic downgrade -1
```

---

## 10. Contacts & Escalation

| Role | Contact | When |
|------|---------|------|
| On-call | alerts@brikonnect.com | Downtime, errors |
| DevOps | devops@brikonnect.com | Infrastructure issues |
| Security | security@brikonnect.com | Security incidents |

---

## Quick Reference

```bash
# Start all
docker compose -f docker-compose.prod.yml up -d

# Stop all
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Shell into container
docker compose -f docker-compose.prod.yml exec api bash

# Run migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Database console
docker compose -f docker-compose.prod.yml exec db psql -U brikonnect

# Redis console
docker compose -f docker-compose.prod.yml exec redis redis-cli
```
