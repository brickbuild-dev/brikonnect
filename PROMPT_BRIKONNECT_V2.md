# Brikonnect Platform — Prompt de Implementação v2

> **Para o Agente Codex:** Este documento contém a especificação completa para implementar a plataforma Brikonnect. Segue os milestones na ordem (M1→M6) e usa as decisões técnicas já definidas. Não precisa de tomar decisões arquiteturais — tudo está especificado.

---

## TL;DR — Resumo Executivo

### O que é
Plataforma SaaS para vendedores LEGO: inventory + orders + picking + sync + shipping.

### Stack
- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + Arq (jobs)
- **Frontend:** React 18 + TypeScript + Vite + TanStack Query + Tailwind + shadcn/ui
- **Extension:** Chrome MV3 + React (Side Panel)
- **Monorepo:** Turborepo + pnpm

### Domínios
- `{tenant}.brikonnect.com` — App por cliente
- `api.brikonnect.com` — API

### Billing
- **Lite (1%):** Picking + Sync apenas
- **Full (2.5%):** Tudo (2% se tiver loja Brikick)
- Fatura dia 1, vence dia 5, mínimo €10/EU ou $5/US

### Funcionalidades Chave
1. Multi-reference search (BrickLink + BrickOwl + Brikick IDs)
2. Brickognize (reconhecimento visual de peças)
3. 15 shipping carriers
4. Catalog cache (Rebrickable + BrickLink dumps)
5. Dark/Light mode

### Milestones
1. **M1:** Auth + Tenants + Users + RBAC
2. **M2:** Inventory + Locations
3. **M3:** Orders + Status
4. **M4:** Picker + Extension
5. **M5:** Audit + Revert
6. **M6:** Sync Engine

---

## Visão do Produto

**Brikonnect** é uma plataforma SaaS para vendedores LEGO que unifica:
- Gestão de inventário multi-canal (BrickLink, BrickOwl, Brikick, Shopify, eBay)
- Sincronização bidirecional de inventário entre canais
- Fulfillment completo: picking → packing → shipping → tracking
- Analytics e relatórios de performance
- API pública + webhooks para integrações

**Diferenciador crítico:** Arquitetura modular que permite reutilizar módulos core (Inventory, Orders, Picker) em outras plataformas (ex: marketplace Brikick) sem carregar o SaaS completo.

---

## Configuração do Domínio

| Tipo | URL | Descrição |
|------|-----|-----------|
| Marketing site | `www.brikonnect.com` | Landing page, docs, pricing |
| App (tenant) | `{tenant}.brikonnect.com` | Cada cliente tem subdomínio próprio |
| API | `api.brikonnect.com` | Endpoint centralizado da API |
| CDN/Assets | `cdn.brikonnect.com` | Ficheiros estáticos (opcional) |

### Tenant Resolution
O backend extrai o tenant do header `Host`:
```python
# middleware
def get_tenant_from_host(request: Request) -> str:
    host = request.headers.get("host", "")
    # demo.brikonnect.com → "demo"
    subdomain = host.split(".")[0]
    return subdomain
```

---

## Configurações Globais

| Setting | Valor | Notas |
|---------|-------|-------|
| **Idioma UI** | Inglês (EN) | Simplificado, língua internacional |
| **Moedas suportadas** | EUR, USD, GBP | Tenant escolhe a sua moeda base |
| **Timezone** | UTC (storage) | Display no timezone do tenant |
| **Email sender** | `help@brikonnect.com` | Via SMTP configurável |
| **Deploy** | VPS próprio | Docker Compose + Traefik |

### Multi-Currency Support

Cada tenant define a sua moeda base. Preços são armazenados e apresentados nessa moeda.

```sql
-- Currency no tenant
ALTER TABLE tenants ADD COLUMN currency VARCHAR(3) DEFAULT 'EUR';
-- Valores possíveis: EUR, USD, GBP

-- Todos os valores monetários usam NUMERIC(12,4) para precisão
-- Campos: unit_price, cost_basis, subtotal, shipping_cost, etc.
```

**Regras:**
1. Valores armazenados na moeda do tenant (sem conversão automática)
2. Sync entre canais: cada canal pode ter moeda diferente, conversão no momento do sync
3. Reports: mostram na moeda do tenant
4. API: aceita valores na moeda do tenant, retorna na mesma

**Conversão (quando necessário):**
- Rates guardados em `currency_rates` (atualização diária via API externa)
- Usado apenas para sync cross-currency e analytics comparativos

```sql
CREATE TABLE currency_rates (
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate NUMERIC(12,6) NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (from_currency, to_currency)
);
```

---

## Stack Tecnológica (Decisões Finais)

### Backend
| Componente | Tecnologia | Justificação |
|------------|------------|--------------|
| Framework | FastAPI (async) | Performance, typing nativo, OpenAPI auto |
| ORM | SQLAlchemy 2.0 (async) | Type hints, async first-class |
| DB | PostgreSQL 16 | JSONB, reliability, full-text search |
| Migrations | Alembic | Standard para SQLAlchemy |
| Queue/Jobs | **Arq** (Redis) | Async nativo, leve, retry/backoff built-in |
| Cache | Redis | Sessões, rate limiting, job queue |
| Auth | Cookie (web) + JWT (API/ext) | Sessão para UX, tokens para integrações |

### Frontend Web
| Componente | Tecnologia | Justificação |
|------------|------------|--------------|
| Framework | **React 18 + TypeScript** | Ecossistema maduro, melhor tooling |
| Build | Vite | Fastest DX, ESM nativo |
| Server State | TanStack Query v5 | Cache, dedupe, optimistic updates |
| Client State | Zustand | Simples, sem boilerplate |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, componentes acessíveis |
| Router | TanStack Router | Type-safe, loader patterns |
| Forms | React Hook Form + Zod | Validation, performance |

### Chrome Extension
| Componente | Tecnologia | Justificação |
|------------|------------|--------------|
| Framework | React 18 + TypeScript | Consistência com web |
| Manifest | V3 | Requisito Chrome |
| UI Mode | **Side Panel** (principal) + Popup (ações rápidas) |
| Storage | chrome.storage.local | Tokens, preferências |
| Build | Vite + CRXJS | HMR para extensões |

### Monorepo
| Componente | Tecnologia |
|------------|------------|
| Tool | Turborepo |
| Package Manager | pnpm |

---

## Design System

### Theming: Dark Mode + Light Mode

O frontend suporta **dois temas** que o utilizador pode alternar:

| Modo | Descrição |
|------|-----------|
| **Light** | Tema claro, padrão para novos utilizadores |
| **Dark** | Tema escuro, reduz fatiga visual |
| **System** | Segue preferência do OS (prefers-color-scheme) |

### Implementação (Tailwind + shadcn/ui)

```tsx
// Theme context com persistência
interface ThemeConfig {
  mode: 'light' | 'dark' | 'system';
  resolvedMode: 'light' | 'dark'; // Actual applied theme
}

// CSS Variables approach (tailwind.config.js)
// Dark mode via class strategy: <html class="dark">
module.exports = {
  darkMode: 'class',
  // ...
}

// Theme toggle persisted in:
// - Web: localStorage + user preferences in DB
// - Extension: chrome.storage.local
```

### Design Tokens (Base)

```css
/* Light mode */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --muted: 210 40% 96%;
  --accent: 210 40% 96%;
  --destructive: 0 84.2% 60.2%;
  --border: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
}

/* Dark mode */
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --muted: 217.2 32.6% 17.5%;
  --accent: 217.2 32.6% 17.5%;
  --destructive: 0 62.8% 30.6%;
  --border: 217.2 32.6% 17.5%;
  --ring: 224.3 76.3% 48%;
}
```

### UI Components (shadcn/ui)

Componentes pré-configurados com suporte a dark mode:
- Button, Input, Select, Checkbox, Radio
- Card, Dialog, Sheet, Dropdown
- Table, DataTable (com sorting/filtering)
- Tabs, Accordion, Collapsible
- Toast, Alert, Badge
- Calendar, DatePicker
- Command (search palette)

### Responsive Breakpoints

| Breakpoint | Width | Target |
|------------|-------|--------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Large desktop |
| `2xl` | 1536px | Extra large |

**Mobile-first approach:** Componentes base para mobile, ajustados em breakpoints maiores.

### Extension UI

A extensão usa o mesmo design system (packages/ui), garantindo:
- Consistência visual entre web e extension
- Mesmo toggle dark/light
- Componentes reutilizados

---

## Estrutura do Repositório

```
/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/           # Config, security, logging
│   │   │   ├── modules/        # Domínios (ver abaixo)
│   │   │   ├── integrations/   # Adapters externos
│   │   │   └── jobs/           # Arq tasks
│   │   ├── alembic/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── web/                    # React Admin UI
│   │   ├── src/
│   │   │   ├── features/       # Feature modules
│   │   │   ├── components/     # Shared components
│   │   │   ├── hooks/          # Custom hooks
│   │   │   ├── lib/            # Utils, API client
│   │   │   └── routes/         # Page components
│   │   └── package.json
│   │
│   └── extension/              # Chrome Extension
│       ├── src/
│       │   ├── sidepanel/      # Side panel UI
│       │   ├── popup/          # Quick actions
│       │   ├── background/     # Service worker
│       │   └── shared/         # Shared with sidepanel/popup
│       ├── manifest.json
│       └── package.json
│
├── packages/
│   ├── sdk/                    # TypeScript API client
│   │   ├── src/
│   │   │   ├── client.ts       # Fetch wrapper
│   │   │   ├── types.ts        # Shared types (generated)
│   │   │   └── endpoints/      # Per-module methods
│   │   └── package.json
│   │
│   └── ui/                     # Shared React components
│       ├── src/
│       └── package.json
│
├── docker-compose.yml
├── turbo.json
└── pnpm-workspace.yaml
```

---

## Módulos Backend (Estrutura por Domínio)

Cada módulo em `app/modules/<domain>/` contém:
```
<domain>/
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas (request/response)
├── service.py     # Business logic (não depende de FastAPI)
├── router.py      # API endpoints /api/v1/<domain>/*
├── deps.py        # Dependencies (auth, tenant, rbac)
└── events.py      # Domain events (opcional)
```

### Lista de Módulos

| Módulo | Camada | Descrição |
|--------|--------|-----------|
| `auth` | Core | Login, sessões, tokens, refresh/revoke |
| `tenants` | SaaS | Gestão de tenants, settings |
| `users` | Core | CRUD users, perfis |
| `rbac` | Core | Roles, permissões, enforcement |
| `stores` | Core | Lojas/canais por tenant |
| `inventory` | Core | Items, locations, stock |
| `orders` | Core | Pedidos, linhas, status |
| `picker` | Core | Sessões picking, rotas, eventos |
| `sync` | Core | Engine de sincronização BL↔BO |
| `shipping` | Core | Etiquetas, carriers, tracking |
| `audit` | Core | Log de alterações, revert |
| `events` | Core | Event bus interno |
| `jobs` | Core | Progress tracking, checkpoints |
| `api_keys` | SaaS | Chaves API para integrações |
| `webhooks` | SaaS | Outbound webhooks |
| `billing` | SaaS | Planos, limites, gating |
| `reports` | SaaS | Relatórios, analytics |
| `definitions` | Shared | Enums, códigos, constantes |

---

## Modelo de Dados

### 1. Tenancy & Auth

```sql
-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    plan VARCHAR(20) NOT NULL DEFAULT 'free', -- free/starter/pro
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(320) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(tenant_id, email)
);
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL, -- owner/admin/staff/picker/readonly
    permissions TEXT[] NOT NULL DEFAULT '{}',
    is_system BOOLEAN DEFAULT false,
    UNIQUE(tenant_id, name)
);

-- User Roles (M:N)
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Sessions (cookie auth)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    user_agent TEXT,
    ip_address INET,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Refresh Tokens (API/extension)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    family_id UUID NOT NULL, -- Para rotation detection
    revoked_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
```

### 2. Stores & Integrations

```sql
-- Stores (canais de venda)
CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    channel VARCHAR(30) NOT NULL, 
    -- Supported channels: bricklink, brickowl, brikick, shopify, ebay, etsy, local
    name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false, -- Source of truth para sync
    settings JSONB DEFAULT '{}',
    -- Settings example: {currency, language, auto_sync, sync_interval_hours}
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_stores_tenant ON stores(tenant_id);
CREATE UNIQUE INDEX idx_stores_primary ON stores(tenant_id) WHERE is_primary = true;

-- Supported Channels:
-- | Channel    | API Type    | Sync Support | Notes |
-- |------------|-------------|--------------|-------|
-- | bricklink  | OAuth 1.0a  | Full         | 5000 req/day limit |
-- | brickowl   | API Key     | Full         | |
-- | brikick    | API Key     | Full         | Internal marketplace |
-- | shopify    | OAuth 2.0   | Full         | |
-- | ebay       | OAuth 2.0   | Orders only  | Complex inventory mapping |
-- | etsy       | OAuth 2.0   | Orders only  | |
-- | local      | N/A         | N/A          | Manual/offline inventory |

-- Store Credentials (encrypted)
CREATE TABLE store_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL UNIQUE REFERENCES stores(id) ON DELETE CASCADE,
    encrypted_data BYTEA NOT NULL,
    encryption_key_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Store Sync State
CREATE TABLE store_sync_state (
    store_id UUID PRIMARY KEY REFERENCES stores(id) ON DELETE CASCADE,
    last_inventory_sync TIMESTAMPTZ,
    last_orders_sync TIMESTAMPTZ,
    last_error TEXT,
    rate_limit_state JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 3. Inventory

```sql
-- Inventory Items (consolidated internal view)
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Identity
    item_type VARCHAR(20) NOT NULL, -- PART/SET/MINIFIG/GEAR/BOOK
    item_no VARCHAR(64) NOT NULL,   -- Canonical part number
    color_id INTEGER,               -- BrickLink color ID (NULL for sets)
    condition VARCHAR(10) NOT NULL, -- NEW/USED
    
    -- Stock
    qty_available INTEGER NOT NULL DEFAULT 0,
    qty_reserved INTEGER NOT NULL DEFAULT 0,
    
    -- Pricing
    unit_price NUMERIC(12,4),
    currency VARCHAR(3) DEFAULT 'EUR',
    cost_basis NUMERIC(12,4),
    
    -- Metadata
    description TEXT,
    remarks TEXT,
    is_retain BOOLEAN DEFAULT false,
    is_stock_room BOOLEAN DEFAULT false,
    
    -- Concurrency
    version INTEGER NOT NULL DEFAULT 1,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_inventory_tenant ON inventory_items(tenant_id);
CREATE INDEX idx_inventory_lookup ON inventory_items(tenant_id, item_type, item_no, color_id, condition);

-- External IDs (mapping para canais)
CREATE TABLE inventory_external_ids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    external_lot_id VARCHAR(64),
    external_inventory_id VARCHAR(64),
    last_synced_at TIMESTAMPTZ,
    UNIQUE(store_id, external_lot_id)
);
CREATE INDEX idx_ext_ids_item ON inventory_external_ids(inventory_item_id);

-- Locations (warehouse organization)
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code VARCHAR(30) NOT NULL,
    zone VARCHAR(20),
    aisle VARCHAR(10),
    shelf VARCHAR(10),
    bin VARCHAR(10),
    sort_order INTEGER DEFAULT 0,
    UNIQUE(tenant_id, code)
);

-- Item Locations (M:N with qty)
CREATE TABLE inventory_item_locations (
    inventory_item_id UUID REFERENCES inventory_items(id) ON DELETE CASCADE,
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    qty INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (inventory_item_id, location_id)
);
```

### 4. Orders

```sql
-- Order Status Enum
-- NEW → PENDING → PICKING → PACKING → READY → SHIPPED → DELIVERED → COMPLETED
-- (can also → CANCELLED, REFUNDED at various stages)

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id),
    
    -- External reference
    external_order_id VARCHAR(64) NOT NULL,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'NEW',
    status_changed_at TIMESTAMPTZ DEFAULT now(),
    
    -- Buyer info
    buyer_name VARCHAR(200),
    buyer_email VARCHAR(320),
    buyer_username VARCHAR(100),
    
    -- Shipping
    ship_to JSONB, -- {name, address1, address2, city, state, postal, country, phone}
    shipping_method VARCHAR(50),
    
    -- Totals
    subtotal NUMERIC(12,2),
    shipping_cost NUMERIC(12,2),
    tax_amount NUMERIC(12,2),
    discount_amount NUMERIC(12,2),
    grand_total NUMERIC(12,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Timestamps
    ordered_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(store_id, external_order_id)
);
CREATE INDEX idx_orders_tenant ON orders(tenant_id);
CREATE INDEX idx_orders_status ON orders(tenant_id, status);
CREATE INDEX idx_orders_date ON orders(tenant_id, ordered_at DESC);

-- Order Lines
CREATE TABLE order_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    -- Item reference
    inventory_item_id UUID REFERENCES inventory_items(id),
    
    -- Item data (snapshot)
    item_type VARCHAR(20) NOT NULL,
    item_no VARCHAR(64) NOT NULL,
    color_id INTEGER,
    color_name VARCHAR(50),
    condition VARCHAR(10),
    description TEXT,
    
    -- Quantities
    qty_ordered INTEGER NOT NULL,
    qty_picked INTEGER DEFAULT 0,
    qty_missing INTEGER DEFAULT 0,
    
    -- Pricing
    unit_price NUMERIC(12,4),
    line_total NUMERIC(12,2),
    
    -- Status
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/PICKED/PARTIAL/MISSING
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_order_lines_order ON order_lines(order_id);
CREATE INDEX idx_order_lines_inventory ON order_lines(inventory_item_id);
```

### 5. Picker

```sql
-- Pick Sessions
CREATE TABLE pick_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', -- DRAFT/ACTIVE/COMPLETED/CANCELLED
    
    -- Stats
    total_orders INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    picked_items INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_pick_sessions_tenant ON pick_sessions(tenant_id);
CREATE INDEX idx_pick_sessions_status ON pick_sessions(tenant_id, status);

-- Pick Session Orders (M:N)
CREATE TABLE pick_session_orders (
    pick_session_id UUID REFERENCES pick_sessions(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    batch_code VARCHAR(10), -- Para agrupar pedidos (A, B, C...)
    PRIMARY KEY (pick_session_id, order_id)
);

-- Pick Events (histórico granular)
CREATE TABLE pick_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pick_session_id UUID NOT NULL REFERENCES pick_sessions(id) ON DELETE CASCADE,
    order_line_id UUID NOT NULL REFERENCES order_lines(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    event_type VARCHAR(20) NOT NULL, -- PICKED/MISSING/ADJUSTMENT
    qty INTEGER NOT NULL,
    
    -- Location snapshot
    location_code VARCHAR(30),
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_pick_events_session ON pick_events(pick_session_id);
```

### 6. Sync Engine

```sql
-- Sync Runs
CREATE TABLE sync_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    source_store_id UUID NOT NULL REFERENCES stores(id),
    target_store_id UUID NOT NULL REFERENCES stores(id),
    
    mode VARCHAR(20) NOT NULL, -- PREVIEW/APPLY
    direction VARCHAR(20) NOT NULL, -- SOURCE_TO_TARGET/BIDIRECTIONAL
    
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- PENDING → FETCHING → COMPARING → PREVIEW_READY → APPLYING → COMPLETED/FAILED
    
    -- Plan summary
    plan_summary JSONB, -- {add: N, update: N, remove: N, unmatched: N}
    
    -- Execution
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Approval
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_sync_runs_tenant ON sync_runs(tenant_id);

-- Sync Plan Items
CREATE TABLE sync_plan_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_run_id UUID NOT NULL REFERENCES sync_runs(id) ON DELETE CASCADE,
    
    action VARCHAR(20) NOT NULL, -- ADD/UPDATE/REMOVE/SKIP
    skip_reason VARCHAR(50), -- UNMATCHED/NO_CHANGE/USER_EXCLUDED
    
    -- References
    inventory_item_id UUID REFERENCES inventory_items(id),
    source_external_id VARCHAR(64),
    target_external_id VARCHAR(64),
    
    -- Diff
    before_state JSONB,
    after_state JSONB,
    changes JSONB, -- [{field, old, new}]
    
    -- Execution
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/APPLIED/FAILED/SKIPPED
    error_message TEXT,
    applied_at TIMESTAMPTZ
);
CREATE INDEX idx_sync_plan_run ON sync_plan_items(sync_run_id);
```

### 7. Shipping

```sql
-- Shipping Carriers (configuração por tenant)
CREATE TABLE shipping_carriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    carrier_code VARCHAR(30) NOT NULL,
    -- Supported: sendcloud, shipstation, pirateship, dhl_global, deutsche_post,
    -- postnl, royal_mail, postnord, myparcel, shipmondo, spring_gds,
    -- australia_post, canada_post, chitchats, stallion_express
    
    display_name VARCHAR(100),
    is_enabled BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    
    -- Credentials (encrypted)
    credentials_encrypted BYTEA,
    credentials_key_id VARCHAR(50),
    
    -- Settings
    settings JSONB DEFAULT '{}', -- {default_service, label_format, etc}
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(tenant_id, carrier_code)
);

CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id),
    carrier_id UUID REFERENCES shipping_carriers(id),
    
    carrier_code VARCHAR(30) NOT NULL,
    service_level VARCHAR(50),
    
    tracking_number VARCHAR(100),
    tracking_url TEXT,
    
    label_url TEXT,
    label_data BYTEA, -- Label PDF/PNG stored directly
    label_format VARCHAR(10), -- PDF/PNG/ZPL
    
    status VARCHAR(20) DEFAULT 'PENDING',
    -- PENDING → LABEL_CREATED → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED → RETURNED
    
    ship_date DATE,
    estimated_delivery DATE,
    actual_delivery DATE,
    
    -- Package details
    weight_grams INTEGER,
    dimensions JSONB, -- {length, width, height, unit}
    
    -- Cost
    cost NUMERIC(10,2),
    currency VARCHAR(3),
    
    -- External reference
    external_shipment_id VARCHAR(100),
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);
CREATE INDEX idx_shipments_status ON shipments(tenant_id, status);
```

### Shipping Carriers Suportados

| Carrier | Code | Região | API Type |
|---------|------|--------|----------|
| SendCloud | `sendcloud` | EU | REST API |
| ShipStation | `shipstation` | Global | REST API |
| PirateShip | `pirateship` | US | REST API |
| DHL Global Mail | `dhl_global` | Global | REST API |
| Deutsche Post | `deutsche_post` | DE/EU | REST API |
| PostNL | `postnl` | NL/EU | REST API |
| Royal Mail Click & Drop | `royal_mail` | UK | REST API |
| PostNord | `postnord` | Nordic | REST API |
| MyParcel | `myparcel` | NL/BE | REST API |
| Shipmondo | `shipmondo` | Nordic | REST API |
| Spring GDS | `spring_gds` | Global | REST API |
| Australia Post | `australia_post` | AU | REST API |
| Canada Post | `canada_post` | CA | REST API |
| ChitChats | `chitchats` | CA | REST API |
| Stallion Express | `stallion_express` | CA/US | REST API |

**Implementação:** Adapter pattern — cada carrier implementa interface comum:
```python
class ShippingAdapter(Protocol):
    async def get_rates(self, package: Package, destination: Address) -> list[Rate]
    async def create_label(self, shipment: ShipmentRequest) -> LabelResponse
    async def track(self, tracking_number: str) -> TrackingInfo
    async def cancel(self, shipment_id: str) -> bool
```

### 8. LEGO Catalog (Cache System)

O catálogo LEGO é construído incrementalmente através de:
- **Rebrickable API** — Dados de peças, sets, cores (tem API key)
- **BrickLink Catalog** — Ficheiros dump periódicos
- **Cache local** — Pesquisas dos users alimentam a DB

```sql
-- Catalog Items (cache crescente)
CREATE TABLE catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identity
    item_type VARCHAR(20) NOT NULL, -- PART/SET/MINIFIG/GEAR/BOOK/CATALOG/INSTRUCTION
    item_no VARCHAR(64) NOT NULL,
    
    -- Basic info
    name VARCHAR(500) NOT NULL,
    category_id INTEGER,
    category_name VARCHAR(200),
    
    -- Dimensions/Weight (when known)
    weight_grams NUMERIC(10,2),
    dimensions JSONB, -- {length, width, height, unit}
    
    -- Images
    image_url TEXT,
    thumbnail_url TEXT,
    
    -- Year info (for sets)
    year_released INTEGER,
    year_ended INTEGER,
    
    -- Additional data
    alternate_nos TEXT[], -- Alternate part numbers
    
    -- Source tracking
    source VARCHAR(20) NOT NULL, -- rebrickable/bricklink/manual
    source_updated_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(item_type, item_no)
);
CREATE INDEX idx_catalog_type_no ON catalog_items(item_type, item_no);
CREATE INDEX idx_catalog_name ON catalog_items USING gin(to_tsvector('english', name));

-- Catalog Colors
CREATE TABLE catalog_colors (
    id INTEGER PRIMARY KEY, -- BrickLink color ID
    name VARCHAR(100) NOT NULL,
    rgb VARCHAR(6), -- Hex color without #
    
    -- Mappings to other systems
    brickowl_id INTEGER,
    rebrickable_id INTEGER,
    ldraw_id INTEGER,
    lego_ids INTEGER[], -- LEGO color IDs (can be multiple)
    
    -- Type
    color_type VARCHAR(20), -- Solid/Transparent/Chrome/Pearl/etc
    
    source VARCHAR(20) DEFAULT 'bricklink',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Catalog Categories
CREATE TABLE catalog_categories (
    id INTEGER PRIMARY KEY, -- BrickLink category ID
    name VARCHAR(200) NOT NULL,
    parent_id INTEGER REFERENCES catalog_categories(id),
    
    source VARCHAR(20) DEFAULT 'bricklink',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Item-Color availability (which colors exist for which parts)
CREATE TABLE catalog_item_colors (
    item_type VARCHAR(20) NOT NULL,
    item_no VARCHAR(64) NOT NULL,
    color_id INTEGER NOT NULL REFERENCES catalog_colors(id),
    
    -- Known quantities in existence (optional, from BrickLink)
    qty_known INTEGER,
    
    source VARCHAR(20) DEFAULT 'bricklink',
    created_at TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (item_type, item_no, color_id)
);
CREATE INDEX idx_item_colors_item ON catalog_item_colors(item_type, item_no);

-- Set Inventories (parts in a set)
CREATE TABLE catalog_set_items (
    set_no VARCHAR(64) NOT NULL,
    
    item_type VARCHAR(20) NOT NULL,
    item_no VARCHAR(64) NOT NULL,
    color_id INTEGER REFERENCES catalog_colors(id),
    
    qty INTEGER NOT NULL DEFAULT 1,
    is_spare BOOLEAN DEFAULT false,
    is_counterpart BOOLEAN DEFAULT false,
    
    source VARCHAR(20) DEFAULT 'rebrickable',
    created_at TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (set_no, item_type, item_no, color_id, is_spare)
);
CREATE INDEX idx_set_items_set ON catalog_set_items(set_no);
```

### Multi-Reference Search System

Cada plataforma (BrickLink, BrickOwl, Brikick) tem os seus próprios IDs para a mesma peça.
O sistema suporta pesquisa por **qualquer referência** e mapeia automaticamente.

```sql
-- Mapeamento de IDs entre plataformas
CREATE TABLE catalog_id_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Canonical reference (internal)
    item_type VARCHAR(20) NOT NULL,
    canonical_item_no VARCHAR(64) NOT NULL, -- Usamos BrickLink como base
    
    -- Platform-specific IDs
    bricklink_id VARCHAR(64),
    brickowl_id VARCHAR(64),
    brikick_id VARCHAR(64), -- Futuro
    rebrickable_id VARCHAR(64),
    lego_element_ids TEXT[], -- LEGO element IDs (podem ser múltiplos)
    
    -- Confidence
    mapping_source VARCHAR(20), -- manual/rebrickable/auto
    confidence NUMERIC(3,2) DEFAULT 1.0, -- 0.0-1.0
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(item_type, canonical_item_no)
);

-- Índices para pesquisa por qualquer ID
CREATE INDEX idx_mapping_bricklink ON catalog_id_mappings(bricklink_id);
CREATE INDEX idx_mapping_brickowl ON catalog_id_mappings(brickowl_id);
CREATE INDEX idx_mapping_brikick ON catalog_id_mappings(brikick_id);
CREATE INDEX idx_mapping_rebrickable ON catalog_id_mappings(rebrickable_id);
```

### Search Flow (Multi-Reference)

```
USER SEARCHES: "973pb0001" (pode ser BrickLink, BrickOwl, ou qualquer)
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. SEARCH catalog_id_mappings                          │
│    WHERE bricklink_id = '973pb0001'                    │
│       OR brickowl_id = '973pb0001'                     │
│       OR brikick_id = '973pb0001'                      │
│       OR canonical_item_no = '973pb0001'               │
│       OR rebrickable_id = '973pb0001'                  │
└─────────────────────────────────────────────────────────┘
                    ↓
         FOUND? → Return canonical + all platform IDs
                    ↓
         NOT FOUND? → Query external APIs
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Query Rebrickable API (has good cross-references)   │
│ 3. Query BrickLink/BrickOwl if needed                  │
│ 4. Cache result in catalog_id_mappings                 │
└─────────────────────────────────────────────────────────┘
                    ↓
         Return unified result with all platform IDs
```

### Search API Response

```json
{
  "item_type": "PART",
  "canonical_id": "973pb0001",
  "name": "Torso with Pattern",
  "image_url": "https://...",
  "platform_ids": {
    "bricklink": "973pb0001",
    "brickowl": "973pb0001c01",
    "brikick": "PART-973-0001",
    "rebrickable": "973pr0001",
    "lego_elements": ["6138623", "4275815"]
  },
  "colors_available": [...]
}
```

---

### Brickognize Integration (Visual Part Recognition)

Integração com **www.brickognize.com** para identificação visual de peças LEGO.

**Casos de uso:**
1. **Adicionar ao inventário** — Utilizador não sabe o ID, tira foto, sistema identifica
2. **Pesquisa** — Pesquisa por imagem em vez de texto/ID

```sql
-- Brickognize API cache (evitar requests repetidos para mesma imagem)
CREATE TABLE brickognize_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    image_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA256 da imagem
    
    -- Results
    predictions JSONB NOT NULL, -- Array of {item_no, confidence, name}
    top_prediction_item_no VARCHAR(64),
    top_prediction_confidence NUMERIC(4,3),
    
    -- Mapping to our catalog
    matched_catalog_item_id UUID REFERENCES catalog_items(id),
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_brickognize_hash ON brickognize_cache(image_hash);
```

### Brickognize Flow

```
USER UPLOADS IMAGE (from camera/file)
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Calculate image hash (SHA256)                       │
│ 2. Check brickognize_cache for existing result         │
└─────────────────────────────────────────────────────────┘
                    ↓
         CACHED? → Return cached predictions
                    ↓
         NOT CACHED? 
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Call Brickognize API                                │
│    POST https://api.brickognize.com/predict/           │
│    Body: multipart/form-data with image                │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Process predictions                                  │
│    - Map item_no to our catalog_id_mappings            │
│    - Cache results                                      │
│    - Return top predictions with platform IDs          │
└─────────────────────────────────────────────────────────┘
```

### Brickognize API Endpoints

```yaml
# Identify part from image
POST   /inventory/identify
       Content-Type: multipart/form-data
       Body: { image: <file> }
       Response: {
         predictions: [
           {
             item_no: "3001",
             name: "Brick 2 x 4",
             confidence: 0.95,
             image_url: "...",
             platform_ids: {...}
           },
           ...
         ],
         top_match: {...}
       }

# Search by image
POST   /search/image
       Content-Type: multipart/form-data
       Body: { image: <file> }
       Response: Same as above + inventory matches if in stock
```

### UI Integration Points

**1. Inventory → Add Item**
```
┌────────────────────────────────────────┐
│  Add Inventory Item                    │
├────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────────┐   │
│  │  📷      │  │ Part ID/Name     │   │
│  │  Take    │  │ [____________]   │   │
│  │  Photo   │  │                  │   │
│  └──────────┘  │ Or search...     │   │
│                └──────────────────┘   │
│                                        │
│  [Identify from Photo]                 │
│                                        │
│  Suggestions:                          │
│  ┌────────────────────────────────┐   │
│  │ 🧱 3001 - Brick 2x4 (95%)     │   │
│  │ 🧱 3002 - Brick 2x3 (78%)     │   │
│  └────────────────────────────────┘   │
└────────────────────────────────────────┘
```

**2. Global Search**
```
┌────────────────────────────────────────┐
│  🔍 Search: [___________] [📷]        │
│                                        │
│  Search by:                            │
│  • Part ID (any platform)              │
│  • Name                                │
│  • Image (Brickognize)                 │
└────────────────────────────────────────┘
```

**3. Chrome Extension - Quick Add**
- Camera button no side panel
- Uses device camera directly
- One-tap identify → add to inventory

### Catalog Cache Strategy

```
1. USER SEARCHES for "3001" (2x4 brick)
   ↓
2. CHECK catalog_id_mappings for any platform match
   ↓
3. CHECK catalog_items for full details
   ↓
4. IF NOT FOUND:
   a) Query Rebrickable API (best for cross-refs)
   b) Fallback: Query BrickLink API (rate limited)
   c) Store in catalog_items + catalog_id_mappings
   ↓
5. RETURN cached data with all platform IDs

6. BACKGROUND JOB (nightly):
   - Import BrickLink catalog dumps
   - Import Rebrickable cross-reference tables
   - Refresh stale items (updated_at > 30 days)
   - Build missing id_mappings from Rebrickable
```

### API Rate Limits Management

| Source | Limit | Strategy |
|--------|-------|----------|
| BrickLink | 5000/day | Cache first, API fallback, daily budget tracking |
| Rebrickable | 1 req/sec | Queue requests, bulk fetch where possible |
| BrickOwl | Varies | Same as BrickLink |

```python
# Rate limit tracking
class RateLimitTracker:
    async def can_request(self, source: str) -> bool
    async def record_request(self, source: str) -> None
    async def get_remaining(self, source: str) -> int
```

### 9. Audit & Events

```sql
-- Audit Log (imutável)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    -- Actor
    actor_type VARCHAR(20) NOT NULL, -- USER/SYSTEM/JOB/API_KEY
    actor_id UUID,
    actor_name VARCHAR(100),
    
    -- Action
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    
    -- Changes
    before_state JSONB,
    after_state JSONB,
    
    -- Context
    correlation_id UUID,
    request_id UUID,
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_entity ON audit_log(tenant_id, entity_type, entity_id);
CREATE INDEX idx_audit_date ON audit_log(tenant_id, created_at DESC);

-- Events (for webhooks and internal bus)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    
    -- Processing
    processed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_events_tenant_type ON events(tenant_id, event_type);
CREATE INDEX idx_events_unprocessed ON events(tenant_id) WHERE processed_at IS NULL;

-- Webhooks
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    url TEXT NOT NULL,
    secret VARCHAR(64) NOT NULL,
    
    events TEXT[] NOT NULL, -- ['order.created', 'inventory.updated', ...]
    
    is_enabled BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Webhook Deliveries
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id),
    
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/DELIVERED/FAILED
    
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    
    response_status INTEGER,
    response_body TEXT,
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_webhook_deliveries_pending ON webhook_deliveries(next_retry_at) 
    WHERE status = 'PENDING';
```

### 10. Email & Notifications

```sql
-- Email Templates
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE, -- NULL = system template
    
    template_key VARCHAR(50) NOT NULL, 
    -- Keys: welcome, password_reset, order_confirmation, order_shipped, 
    -- order_delivered, low_stock_alert, sync_completed, sync_failed
    
    subject VARCHAR(200) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    
    variables JSONB DEFAULT '[]', -- [{name, description, example}]
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(tenant_id, template_key)
);

-- Email Queue
CREATE TABLE email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    
    to_email VARCHAR(320) NOT NULL,
    to_name VARCHAR(100),
    
    subject VARCHAR(200) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    
    -- Tracking
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/SENT/FAILED
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Reference
    template_key VARCHAR(50),
    reference_type VARCHAR(50), -- order/user/sync
    reference_id UUID,
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_email_queue_pending ON email_queue(status) WHERE status = 'PENDING';

-- In-app Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL = all users in tenant
    
    type VARCHAR(50) NOT NULL,
    -- Types: order_new, order_status, sync_completed, sync_failed, 
    -- low_stock, system_alert, feature_announcement
    
    title VARCHAR(200) NOT NULL,
    body TEXT,
    
    action_url TEXT,
    action_label VARCHAR(50),
    
    -- Reference
    reference_type VARCHAR(50),
    reference_id UUID,
    
    -- Status
    read_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_notifications_user ON notifications(tenant_id, user_id, read_at);
```

### Email System

**Provider:** SMTP configurável (domínio próprio `help@brikonnect.com`)

```python
# Email service interface
class EmailService:
    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None
    ) -> bool

    async def send_template(
        self,
        to: str,
        template_key: str,
        variables: dict,
        tenant_id: UUID | None = None
    ) -> bool

    async def queue_email(
        self,
        to: str,
        template_key: str,
        variables: dict,
        tenant_id: UUID | None = None
    ) -> UUID  # Returns queue item ID
```

**Templates Padrão:**
| Key | Trigger | Variables |
|-----|---------|-----------|
| `welcome` | User created | `{user_name, tenant_name, login_url}` |
| `password_reset` | Password reset requested | `{user_name, reset_url, expires_in}` |
| `order_confirmation` | Order imported | `{buyer_name, order_no, items_count, total}` |
| `order_shipped` | Status → SHIPPED | `{buyer_name, order_no, tracking_number, tracking_url}` |
| `low_stock_alert` | Stock < threshold | `{item_name, item_no, current_qty, threshold}` |
| `sync_completed` | Sync job done | `{sync_type, items_updated, items_added, items_removed}` |
| `sync_failed` | Sync job failed | `{sync_type, error_message}` |

### 11. Jobs & API Keys

```sql
-- Job Runs (para tracking de long-running tasks)
CREATE TABLE job_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    job_type VARCHAR(50) NOT NULL, -- sync/import/export/label_batch
    
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- PENDING → RUNNING → COMPLETED/FAILED/CANCELLED
    
    -- Progress
    progress_percent INTEGER DEFAULT 0,
    progress_message TEXT,
    progress_data JSONB,
    
    -- Idempotency
    idempotency_key VARCHAR(100),
    
    -- Execution
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_heartbeat_at TIMESTAMPTZ,
    
    error_message TEXT,
    result JSONB,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(tenant_id, idempotency_key)
);
CREATE INDEX idx_job_runs_tenant ON job_runs(tenant_id);
CREATE INDEX idx_job_runs_status ON job_runs(status) WHERE status = 'RUNNING';

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(8) NOT NULL, -- Primeiros 8 chars para identificação
    key_hash VARCHAR(64) NOT NULL,
    
    scopes TEXT[] DEFAULT '{}',
    
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
```

---

## RBAC (Roles & Permissions)

### Roles Predefinidos

| Role | Descrição |
|------|-----------|
| `owner` | Acesso total, pode gerir billing e eliminar tenant |
| `admin` | Gestão completa exceto billing/deletion |
| `staff` | Operações diárias, sem settings sensíveis |
| `picker` | Apenas picking e visualização necessária |
| `readonly` | Apenas visualização |

### Permissions

```
# Format: resource:action

# Inventory
inventory:read
inventory:write
inventory:delete
inventory:import
inventory:export

# Orders
orders:read
orders:write
orders:status_update
orders:cancel
orders:refund

# Picker
picker:read
picker:create_session
picker:pick
picker:manage_sessions

# Stores
stores:read
stores:write
stores:credentials

# Sync
sync:read
sync:preview
sync:apply

# Users/RBAC
users:read
users:write
users:invite
roles:manage

# Audit
audit:read

# Settings
settings:read
settings:write
billing:manage

# API/Webhooks
api_keys:manage
webhooks:manage
```

### Matrix Role → Permissions

| Permission | owner | admin | staff | picker | readonly |
|------------|-------|-------|-------|--------|----------|
| inventory:* | ✓ | ✓ | ✓ | read | read |
| orders:* | ✓ | ✓ | ✓ | read,status | read |
| picker:* | ✓ | ✓ | ✓ | ✓ | read |
| stores:* | ✓ | ✓ | read | - | read |
| sync:* | ✓ | ✓ | preview | - | - |
| users:* | ✓ | ✓ | - | - | - |
| audit:read | ✓ | ✓ | ✓ | - | - |
| settings:* | ✓ | write | read | - | - |
| billing:manage | ✓ | - | - | - | - |
| api_keys:manage | ✓ | ✓ | - | - | - |
| webhooks:manage | ✓ | ✓ | - | - | - |

---

## API Endpoints

### Estrutura Base
- Prefixo: `/api/v1`
- Formato: JSON
- Auth: Cookie session (web) ou Bearer token (API/extension)
- Tenant: Extraído de session/token (não no URL)

### Endpoints por Módulo

```yaml
# Auth
POST   /auth/login              # Cookie session
POST   /auth/logout
POST   /auth/token              # Get access + refresh token
POST   /auth/token/refresh      # Refresh access token
POST   /auth/token/revoke       # Revoke refresh token
GET    /auth/me                 # Current user + tenant info

# Users
GET    /users                   # List users (tenant)
POST   /users                   # Create user
GET    /users/{id}
PATCH  /users/{id}
DELETE /users/{id}
POST   /users/{id}/roles        # Assign role

# Stores
GET    /stores
POST   /stores
GET    /stores/{id}
PATCH  /stores/{id}
DELETE /stores/{id}
POST   /stores/{id}/credentials # Set encrypted credentials
POST   /stores/{id}/test        # Test connection
POST   /stores/{id}/sync        # Trigger manual sync

# Inventory
GET    /inventory                    # List with filters
POST   /inventory                    # Create item
GET    /inventory/{id}
PATCH  /inventory/{id}
DELETE /inventory/{id}
POST   /inventory/bulk               # Bulk create/update
POST   /inventory/import             # Import from file (async job)
GET    /inventory/export             # Export to file

# Locations
GET    /locations
POST   /locations
PATCH  /locations/{id}
DELETE /locations/{id}

# Orders
GET    /orders                       # List with filters
GET    /orders/{id}
PATCH  /orders/{id}                  # Update (limited fields)
POST   /orders/{id}/status           # Change status
GET    /orders/{id}/lines
GET    /orders/{id}/history          # Audit trail

# Picker
GET    /picker/sessions
POST   /picker/sessions              # Create from order IDs
GET    /picker/sessions/{id}
PATCH  /picker/sessions/{id}         # Update status
DELETE /picker/sessions/{id}         # Cancel
GET    /picker/sessions/{id}/route   # Get optimized pick route
POST   /picker/sessions/{id}/pick    # Record pick event
GET    /picker/sessions/{id}/events  # Pick history

# Sync
POST   /sync/preview                 # Create preview (async)
GET    /sync/runs
GET    /sync/runs/{id}
GET    /sync/runs/{id}/plan          # Detailed plan items
POST   /sync/runs/{id}/approve       # Approve and start apply
POST   /sync/runs/{id}/cancel

# Shipping
POST   /shipping/rates               # Get shipping rates
POST   /shipping/labels              # Create label (async)
GET    /shipping/labels/{id}
GET    /shipping/tracking/{number}   # Track shipment

# Audit
GET    /audit                        # List with filters

# Jobs
GET    /jobs/{id}                    # Get job status/progress
GET    /jobs/{id}/logs               # Get job logs

# Webhooks
GET    /webhooks
POST   /webhooks
PATCH  /webhooks/{id}
DELETE /webhooks/{id}
POST   /webhooks/{id}/test           # Send test event

# API Keys
GET    /api-keys
POST   /api-keys
DELETE /api-keys/{id}

# Definitions
GET    /definitions/colors           # BrickLink colors
GET    /definitions/categories       # Item categories
GET    /definitions/item-types       # PART/SET/MINIFIG/etc
GET    /definitions/order-statuses
GET    /definitions/countries

# Health
GET    /health                       # Basic health
GET    /ready                        # DB connectivity check
```

---

## Autenticação

### Web (Cookie Session)
1. `POST /auth/login` com `{email, password}`
2. Backend valida, cria session, retorna cookie `HttpOnly, Secure, SameSite=Lax`
3. Subsequentes requests incluem cookie automaticamente
4. CSRF token via header `X-CSRF-Token` (gerado no login)

### API/Extension (JWT)
1. `POST /auth/token` com `{email, password}`
2. Retorna `{access_token, refresh_token, expires_in}`
3. Access token: 15 min TTL, usado em `Authorization: Bearer <token>`
4. Refresh token: 7 dias TTL, usado para obter novo access token
5. Refresh rotation: cada refresh gera novo refresh_token, invalida anterior

### Extension Flow
1. User abre extension, vê login form
2. Submete credenciais → `POST /auth/token`
3. Extension guarda tokens em `chrome.storage.local`
4. Requests usam access token
5. Background script renova automaticamente antes de expirar
6. Logout: `POST /auth/token/revoke` + limpa storage

---

## Sync Engine (BrickLink ↔ BrickOwl)

### Flow Completo

```
1. USER REQUEST
   POST /sync/preview
   {source_store_id, target_store_id}

2. JOB CREATED
   - Status: PENDING
   - Returns job_id

3. FETCH PHASE (async worker)
   - Fetch inventory from source (via adapter)
   - Fetch inventory from target (via adapter)
   - Status: FETCHING, progress updates

4. COMPARE PHASE
   - Map items by canonical ID (item_no + color + condition)
   - Identify: ADD, UPDATE, REMOVE, UNMATCHED
   - Status: COMPARING

5. PLAN READY
   - Status: PREVIEW_READY
   - User pode ver plan via GET /sync/runs/{id}/plan

6. USER APPROVAL
   POST /sync/runs/{id}/approve
   - Requires admin/owner role
   - Status: APPLYING

7. APPLY PHASE (async worker)
   - For each plan item:
     - Apply change to target via adapter
     - Update local inventory
     - Create audit log
     - Update progress
   - Checkpoint every N items (resume on failure)

8. COMPLETION
   - Status: COMPLETED or FAILED
   - Summary available
```

### Guardrails
- REMOVE: Max 10% do inventário target ou confirmação explícita
- Rate limiting: Respeita API limits de BL/BO (429 → exponential backoff)
- Idempotency: Cada plan item tem ID, retry não duplica
- Rollback parcial: Via audit log (pode reverter item a item)

---

## Chrome Extension

### Funcionalidades

| Feature | Side Panel | Popup |
|---------|------------|-------|
| Login/Logout | ✓ | ✓ |
| Dashboard resumo | ✓ | ✓ |
| Lista de orders | ✓ | - |
| Order detail | ✓ | - |
| Picking flow completo | ✓ | - |
| Quick status update | ✓ | ✓ |
| Quick order lookup | ✓ | ✓ |
| Sync status | ✓ | - |
| Notifications | ✓ | ✓ (badge) |

### Manifest V3 Permissions
```json
{
  "permissions": [
    "storage",
    "sidePanel",
    "notifications",
    "alarms"
  ],
  "host_permissions": [
    "https://api.brikonnect.com/*",
    "http://localhost:8000/*"
  ]
}
```

### Storage Structure
```typescript
// chrome.storage.local
interface ExtensionStorage {
  auth: {
    accessToken: string;
    refreshToken: string;
    expiresAt: number;
    user: {
      id: string;
      email: string;
      tenantId: string;
      permissions: string[];
    };
  };
  settings: {
    apiBaseUrl: string;
    notifications: boolean;
    theme: 'light' | 'dark' | 'system';
  };
  cache: {
    lastOrders: Order[];
    lastSync: Date;
  };
}
```

---

## Milestones de Implementação

### M1: Foundation (Semana 1-2)
**Backend:**
- [x] Setup monorepo (Turborepo + pnpm)
- [ ] Auth module (login, sessions, tokens, refresh/revoke)
- [ ] Tenants module (CRUD básico)
- [ ] Users module (CRUD + roles)
- [ ] RBAC enforcement middleware
- [ ] Migrations base (todas tabelas auth)
- [ ] Seed data (tenant demo + user admin)
- [ ] Tests: auth flow, tenant isolation

**Frontend:**
- [ ] Setup Vite + React
- [ ] Login page
- [ ] Auth context + protected routes
- [ ] Layout base (sidebar, header)
- [ ] Dashboard placeholder

**Done when:**
- `POST /auth/login` retorna cookie válido
- `POST /auth/token` retorna access + refresh
- Token refresh funciona
- Tenant A não vê dados de Tenant B
- UI login → dashboard funciona

---

### M2: Inventory (Semana 2-3)
**Backend:**
- [ ] Inventory module completo
- [ ] Locations module
- [ ] Inventory-location M:N
- [ ] Bulk operations
- [ ] Import/export (job async)
- [ ] Migrations inventory
- [ ] Tests: CRUD, bulk, concurrency

**Frontend:**
- [ ] Inventory list (tabela com filtros)
- [ ] Inventory detail/edit
- [ ] Location management
- [ ] Import dialog

**Done when:**
- CRUD inventory funciona com locations
- Bulk update funciona
- Import cria job e mostra progress
- UI mostra lista filtrada

---

### M3: Orders (Semana 3-4)
**Backend:**
- [ ] Orders module completo
- [ ] Order lines
- [ ] Status transitions (com validação)
- [ ] Order history (via audit)
- [ ] Migrations orders
- [ ] Tests: CRUD, status flow

**Frontend:**
- [ ] Orders list (tabela com filtros)
- [ ] Order detail (linhas, status)
- [ ] Status update actions
- [ ] Order search

**Done when:**
- CRUD orders funciona
- Status transitions validadas
- UI mostra orders com filtros
- Audit trail visível

---

### M4: Picker (Semana 4-5)
**Backend:**
- [ ] Pick sessions module
- [ ] Route optimization (por location)
- [ ] Pick events
- [ ] Update order line status
- [ ] Migrations picker
- [ ] Tests: session flow, events

**Frontend:**
- [ ] Pick sessions list
- [ ] Create session (selecionar orders)
- [ ] Picking UI (rota por location)
- [ ] Pick/missing actions

**Extension:**
- [ ] Setup extension project
- [ ] Login flow
- [ ] Side panel base
- [ ] Picking flow (primary use case)

**Done when:**
- Criar session com múltiplas orders
- Rota otimizada por location
- Pick events registados
- Extension: picking funciona

---

### M5: Audit & Revert (Semana 5-6)
**Backend:**
- [ ] Audit module completo
- [ ] Automatic audit logging (middleware/hooks)
- [ ] Revert capability (single entity)
- [ ] Events module
- [ ] Webhooks module (básico)
- [ ] Tests: audit, revert, webhooks

**Frontend:**
- [ ] Audit log list (filtros)
- [ ] Entity history view
- [ ] Revert action
- [ ] Webhook management

**Done when:**
- Todas alterações criam audit
- Pode reverter alteração individual
- Webhooks disparam em eventos

---

### M6: Sync Engine (Semana 6-8)
**Backend:**
- [ ] Stores module (credentials encriptadas)
- [ ] Integration adapters (BL, BO mocks)
- [ ] Sync module completo
- [ ] Preview job
- [ ] Apply job (com checkpoint)
- [ ] Rate limiting
- [ ] Tests: sync flow end-to-end

**Frontend:**
- [ ] Stores management
- [ ] Sync wizard (select stores → preview → approve)
- [ ] Sync progress view
- [ ] Plan review UI

**Extension:**
- [ ] Sync status widget
- [ ] Quick sync trigger

**Done when:**
- Preview gera plan correto
- Apply executa com progress
- Retry após falha continua do checkpoint
- UI completo para sync

---

## Billing System

### Modelo de Preços: % do GMV (Gross Merchandise Value)

Cobrança baseada numa **percentagem fixa do valor líquido total de encomendas**:
- **Valor líquido** = subtotal dos produtos (SEM portes de envio)
- Soma de TODAS as stores/plataformas associadas ao tenant

### Duas Versões do Produto

| Versão | Features | Taxa GMV | Com Loja Brikick |
|--------|----------|----------|------------------|
| **Brikonnect Lite** | Picking + Sync apenas | **1%** | **1%** |
| **Brikonnect Full** | Todas as funcionalidades | **2.5%** | **2%** |

**Desconto Brikick:** Tenants com loja ativa no Brikick pagam 2% em vez de 2.5% na versão Full.

### Brikonnect Lite vs Full

| Feature | Lite | Full |
|---------|------|------|
| Inventory Management | ✓ | ✓ |
| Orders Management | ✓ | ✓ |
| **Picking System** | ✓ | ✓ |
| **Sync entre Plataformas** | ✓ | ✓ |
| Locations/Warehouse | Basic | Advanced |
| Shipping Labels | ❌ | ✓ |
| Analytics/Reports | Basic | Full |
| API Access | ❌ | ✓ |
| Webhooks | ❌ | ✓ |
| Multi-user | 1 user | Unlimited |
| Brickognize (Visual ID) | ❌ | ✓ |

### Regras de Faturação

```
┌─────────────────────────────────────────────────────────────┐
│  CICLO DE FATURAÇÃO                                         │
├─────────────────────────────────────────────────────────────┤
│  Dia 1 do mês    → Fatura gerada (período: mês anterior)   │
│  Dia 5 do mês    → Vencimento da fatura                    │
│  Após dia 5      → Suspensão se não pago                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MÍNIMO DE FATURAÇÃO                                        │
├─────────────────────────────────────────────────────────────┤
│  EUR: €10 mínimo                                            │
│  USD: $5 mínimo                                             │
│                                                             │
│  Se não atingir → Acumula para o mês seguinte              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MÉTODOS DE PAGAMENTO                                       │
├─────────────────────────────────────────────────────────────┤
│  • Stripe (cartão de crédito)                              │
│  • PayPal                                                   │
│  • Cartão de crédito direto                                │
└─────────────────────────────────────────────────────────────┘
```

### Mudança de Versão (Lite ↔ Full)

User pode mudar de versão **a qualquer momento**. Billing é calculado **pro-rata**:

```
EXEMPLO: Janeiro (31 dias)
─────────────────────────────────────────
Dia 1-10 (10 dias):  Lite  @ 1%
Dia 11-31 (21 dias): Full  @ 2.5%

GMV Total do mês: €10,000

Cálculo:
├─ Lite:  (10/31) × €10,000 × 1%   = €32.26
├─ Full:  (21/31) × €10,000 × 2.5% = €169.35
└─ TOTAL: €201.61
```

### Modelo de Dados

```sql
-- Versões do produto
CREATE TYPE product_version AS ENUM ('lite', 'full');

-- Histórico de versão do tenant (para billing pro-rata)
CREATE TABLE tenant_version_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    version product_version NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ, -- NULL = current version
    
    -- Reason for change
    changed_by UUID REFERENCES users(id),
    change_reason VARCHAR(100), -- upgrade/downgrade/initial
    
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_tenant_version_tenant ON tenant_version_history(tenant_id);
CREATE INDEX idx_tenant_version_active ON tenant_version_history(tenant_id) 
    WHERE ended_at IS NULL;

-- Tenant billing config
ALTER TABLE tenants ADD COLUMN current_version product_version DEFAULT 'lite';
ALTER TABLE tenants ADD COLUMN has_brikick_store BOOLEAN DEFAULT false;
ALTER TABLE tenants ADD COLUMN billing_currency VARCHAR(3) DEFAULT 'EUR';
ALTER TABLE tenants ADD COLUMN billing_email VARCHAR(320);
ALTER TABLE tenants ADD COLUMN stripe_customer_id VARCHAR(100);
ALTER TABLE tenants ADD COLUMN paypal_payer_id VARCHAR(100);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    year_month VARCHAR(7) NOT NULL, -- '2026-01'
    
    -- Amounts
    currency VARCHAR(3) NOT NULL,
    net_gmv NUMERIC(12,2) NOT NULL, -- Total GMV líquido
    
    -- Pro-rata breakdown
    lite_days INTEGER DEFAULT 0,
    lite_gmv NUMERIC(12,2) DEFAULT 0,
    lite_fee NUMERIC(10,2) DEFAULT 0, -- lite_gmv × 1%
    
    full_days INTEGER DEFAULT 0,
    full_gmv NUMERIC(12,2) DEFAULT 0,
    full_fee NUMERIC(10,2) DEFAULT 0, -- full_gmv × 2.5% or 2%
    
    brikick_discount_applied BOOLEAN DEFAULT false,
    
    subtotal NUMERIC(10,2) NOT NULL, -- lite_fee + full_fee
    
    -- Accumulated from previous months (if below minimum)
    accumulated_from_previous NUMERIC(10,2) DEFAULT 0,
    
    total_due NUMERIC(10,2) NOT NULL, -- subtotal + accumulated
    
    -- Minimum threshold
    minimum_threshold NUMERIC(10,2) NOT NULL, -- €10 or $5
    below_minimum BOOLEAN DEFAULT false, -- If true, accumulates to next month
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    -- DRAFT → ISSUED → PAID / OVERDUE → SUSPENDED
    
    issued_at TIMESTAMPTZ,
    due_date DATE, -- Day 5 of the month
    paid_at TIMESTAMPTZ,
    
    -- Payment
    payment_method VARCHAR(20), -- stripe/paypal/card
    payment_reference VARCHAR(100),
    
    -- Store breakdown for transparency
    store_breakdown JSONB,
    -- [{store_id, store_name, channel, orders_count, net_gmv}]
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(tenant_id, year_month)
);
CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due ON invoices(due_date) WHERE status = 'ISSUED';

-- Payment records
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    
    method VARCHAR(20) NOT NULL, -- stripe/paypal/card
    
    -- Provider references
    stripe_payment_intent_id VARCHAR(100),
    paypal_transaction_id VARCHAR(100),
    
    status VARCHAR(20) NOT NULL, -- pending/succeeded/failed/refunded
    
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
```

### Billing Calculation Job

```python
# Runs on day 1 of each month at 00:05 UTC
async def generate_monthly_invoice(tenant_id: UUID, year_month: str):
    """
    1. Get all orders for the period (excluding shipping costs)
    2. Get version history for pro-rata calculation
    3. Check if tenant has Brikick store (for discount)
    4. Calculate fees per version period
    5. Check minimum threshold
    6. Create invoice (or accumulate if below minimum)
    """
    
    tenant = await get_tenant(tenant_id)
    period_start, period_end = get_month_range(year_month)
    total_days = (period_end - period_start).days + 1
    
    # Get version history for the month
    version_periods = await get_version_periods(tenant_id, period_start, period_end)
    
    # Get all orders (net GMV = grand_total - shipping)
    orders = await get_orders_for_period(tenant_id, period_start, period_end)
    total_net_gmv = sum(o.grand_total - (o.shipping_cost or 0) for o in orders)
    
    # Calculate pro-rata
    lite_days = sum(p.days for p in version_periods if p.version == 'lite')
    full_days = sum(p.days for p in version_periods if p.version == 'full')
    
    lite_gmv = total_net_gmv * (lite_days / total_days) if lite_days else 0
    full_gmv = total_net_gmv * (full_days / total_days) if full_days else 0
    
    # Calculate fees
    lite_fee = lite_gmv * Decimal('0.01')  # 1%
    
    # Full fee: 2% if has Brikick store, 2.5% otherwise
    full_rate = Decimal('0.02') if tenant.has_brikick_store else Decimal('0.025')
    full_fee = full_gmv * full_rate
    
    subtotal = lite_fee + full_fee
    
    # Add accumulated from previous months
    accumulated = await get_accumulated_amount(tenant_id)
    total_due = subtotal + accumulated
    
    # Check minimum threshold
    minimum = Decimal('5.00') if tenant.billing_currency == 'USD' else Decimal('10.00')
    below_minimum = total_due < minimum
    
    if below_minimum:
        # Don't issue invoice, accumulate for next month
        await accumulate_for_next_month(tenant_id, total_due)
        return None
    
    # Create invoice
    invoice = Invoice(
        tenant_id=tenant_id,
        period_start=period_start,
        period_end=period_end,
        year_month=year_month,
        currency=tenant.billing_currency,
        net_gmv=total_net_gmv,
        lite_days=lite_days,
        lite_gmv=lite_gmv,
        lite_fee=lite_fee,
        full_days=full_days,
        full_gmv=full_gmv,
        full_fee=full_fee,
        brikick_discount_applied=tenant.has_brikick_store,
        subtotal=subtotal,
        accumulated_from_previous=accumulated,
        total_due=total_due,
        minimum_threshold=minimum,
        below_minimum=False,
        status='ISSUED',
        issued_at=datetime.utcnow(),
        due_date=date(period_end.year, period_end.month, 5),  # Day 5
    )
    
    return invoice


# Runs daily at 00:10 UTC - check for overdue invoices
async def check_overdue_invoices():
    """
    Find invoices past due date and not paid.
    Suspend tenant privileges.
    """
    overdue = await get_overdue_invoices()
    
    for invoice in overdue:
        invoice.status = 'OVERDUE'
        await suspend_tenant(invoice.tenant_id)
        await send_overdue_notification(invoice)
```

### Suspension on Non-Payment

```sql
-- Tenant suspension tracking
ALTER TABLE tenants ADD COLUMN is_suspended BOOLEAN DEFAULT false;
ALTER TABLE tenants ADD COLUMN suspended_at TIMESTAMPTZ;
ALTER TABLE tenants ADD COLUMN suspension_reason VARCHAR(100);

-- What happens when suspended:
-- 1. API returns 402 Payment Required
-- 2. UI shows "Account Suspended" banner with pay button
-- 3. Sync jobs are paused
-- 4. Can still VIEW data but cannot CREATE/UPDATE
-- 5. After payment, auto-reactivate
```

### Billing API Endpoints

```yaml
# Current status
GET    /billing/status           # Current version, accumulated, next invoice estimate

# Invoices
GET    /billing/invoices         # List all invoices
GET    /billing/invoices/{id}    # Invoice detail with breakdown
GET    /billing/invoices/{id}/pdf # Download PDF

# Version management
GET    /billing/version          # Current version (lite/full)
POST   /billing/version          # Change version {version: "lite"|"full"}
GET    /billing/version/history  # Version change history

# Payments
POST   /billing/pay/{invoice_id} # Initiate payment
       Body: {method: "stripe"|"paypal"}
GET    /billing/payment-methods  # Saved payment methods
POST   /billing/payment-methods  # Add payment method

# Webhooks (from Stripe/PayPal)
POST   /billing/webhooks/stripe
POST   /billing/webhooks/paypal
```

### Payment Flow (Stripe Example)

```
1. User clicks "Pay Invoice"
   ↓
2. POST /billing/pay/{invoice_id} {method: "stripe"}
   ↓
3. Backend creates Stripe PaymentIntent
   ↓
4. Returns client_secret to frontend
   ↓
5. Frontend uses Stripe.js to collect card
   ↓
6. Stripe confirms payment
   ↓
7. Webhook received: payment_intent.succeeded
   ↓
8. Update invoice status → PAID
   ↓
9. If tenant was suspended → reactivate
```

---

## Guia de Fracionamento (Reuso em Marketplace)

### Módulos Core (Reutilizáveis)
```
inventory/  → Gestão de stock
orders/     → Gestão de pedidos  
picker/     → Workflow de picking
sync/       → Sincronização (opcional)
audit/      → Logging de alterações
jobs/       → Background tasks
```

### Módulos SaaS (Opcionais)
```
tenants/    → Multi-tenancy (pode ser single-tenant)
billing/    → Planos e limites
webhooks/   → Integrações externas
api_keys/   → Acesso programático
```

### Para Integrar no Marketplace:

**Opção A: SDK + API Gateway**
```typescript
// No marketplace
import { BrikonnectClient } from '@brikonnect/sdk';

const client = new BrikonnectClient({
  baseUrl: 'https://internal-brikonnect/api/v1',
  apiKey: process.env.BRIKONNECT_API_KEY,
});

// Use inventory do Brikonnect
const items = await client.inventory.list({ filters });
```

**Opção B: Embed como Micro-frontend**
```tsx
// Mount Brikonnect UI dentro do marketplace
<BrikonnectProvider config={{...}}>
  <InventoryModule />
  <OrdersModule />
</BrikonnectProvider>
```

**Opção C: Database Sharing**
- Partilhar schema Postgres
- Importar módulos Python como packages
- Desativar módulos SaaS via feature flags

### Feature Flags
```python
# config.py
FEATURES = {
    "multi_tenant": True,      # False para single-tenant
    "billing": True,           # False para desativar planos
    "sync": True,              # False para desativar sync
    "webhooks": True,
    "public_api": True,
}

# Usar em routers
if settings.FEATURES["sync"]:
    api_router.include_router(sync.router)
```

---

## Infraestrutura (VPS + Docker)

### Arquitetura de Deploy

```
                    ┌─────────────────────────────────────────────┐
                    │                    VPS                       │
                    │                                             │
    Internet ──────►│  ┌─────────┐      ┌─────────┐              │
                    │  │ Traefik │──────│   API   │              │
    *.brikonnect.com│  │ :80/443 │      │  :8000  │              │
                    │  └─────────┘      └────┬────┘              │
                    │       │                │                    │
                    │       │           ┌────┴────┐              │
                    │       │           │ Worker  │              │
                    │       │           │  (Arq)  │              │
                    │       │           └────┬────┘              │
                    │       │                │                    │
                    │  ┌────┴────┐      ┌────┴────┐              │
                    │  │   Web   │      │  Redis  │              │
                    │  │  :3000  │      │  :6379  │              │
                    │  └─────────┘      └─────────┘              │
                    │                                             │
                    │  ┌─────────┐      ┌─────────┐              │
                    │  │ Postgres│      │ (Other  │              │
                    │  │  :5432  │      │ services)│              │
                    │  └─────────┘      └─────────┘              │
                    └─────────────────────────────────────────────┘
```

### Docker Compose (Production-Ready)

```yaml
# docker-compose.yml
version: "3.9"

services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@brikonnect.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "traefik_certs:/letsencrypt"
    labels:
      - "traefik.enable=true"
      # Dashboard (optional, protect in production)
      - "traefik.http.routers.dashboard.rule=Host(`traefik.brikonnect.com`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.middlewares=auth"
    networks:
      - brikonnect

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - brikonnect

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - brikonnect

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=*.brikonnect.com,localhost
      - CORS_ORIGINS=https://*.brikonnect.com
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      # API routes
      - "traefik.http.routers.api.rule=Host(`api.brikonnect.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=8000"
      # Tenant API (wildcard)
      - "traefik.http.routers.api-tenant.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api-tenant.entrypoints=websecure"
      - "traefik.http.routers.api-tenant.tls.certresolver=letsencrypt"
    networks:
      - brikonnect

  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    command: arq app.jobs.worker.WorkerSettings
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - brikonnect

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    labels:
      - "traefik.enable=true"
      # Tenant subdomains serve the web app
      - "traefik.http.routers.web.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`) && !PathPrefix(`/api`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=3000"
    networks:
      - brikonnect

networks:
  brikonnect:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  traefik_certs:
```

### Environment Variables (.env)

```bash
# Database
POSTGRES_DB=brikonnect
POSTGRES_USER=brikonnect
POSTGRES_PASSWORD=<strong-password>

# Security
SECRET_KEY=<64-char-random-string>
ENCRYPTION_KEY=<32-char-key-for-credentials>

# External APIs
REBRICKABLE_API_KEY=<your-key>
BRICKLINK_CONSUMER_KEY=<your-key>
BRICKLINK_CONSUMER_SECRET=<your-secret>
BRICKLINK_TOKEN=<your-token>
BRICKLINK_TOKEN_SECRET=<your-token-secret>

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=help@brikonnect.com
SMTP_PASSWORD=<password>
SMTP_FROM=help@brikonnect.com

# Optional: Sentry for error tracking
SENTRY_DSN=<your-sentry-dsn>
```

---

## Execução (Comandos)

### Desenvolvimento Local

```bash
# Setup inicial
pnpm install
docker compose -f docker-compose.dev.yml up -d db redis

# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed  # Criar dados iniciais
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Worker (Arq) - outro terminal
arq app.jobs.worker.WorkerSettings

# Frontend - outro terminal
cd apps/web
pnpm dev

# Extension - outro terminal
cd apps/extension
pnpm dev
```

### Produção (VPS)

```bash
# Clone e setup
git clone https://github.com/brickbuild-dev/brikonnect.git
cd brikonnect
cp .env.example .env
# Edit .env with production values

# Build e start
docker compose up -d --build

# Migrations
docker compose exec api alembic upgrade head

# Seed inicial (apenas primeira vez)
docker compose exec api python -m app.seed

# Logs
docker compose logs -f api worker

# Update
git pull
docker compose up -d --build
docker compose exec api alembic upgrade head
```

### Testes

```bash
# Backend
cd apps/api
pytest -v
pytest --cov=app --cov-report=html  # Coverage report

# Frontend
cd apps/web
pnpm test
pnpm test:e2e  # Playwright E2E

# Extension
cd apps/extension
pnpm test
```

---

## Checklist Final MVP

- [ ] Multi-tenant isolado (testes comprovam)
- [ ] Auth completo (cookie + JWT + refresh)
- [ ] RBAC funcional (picker só vê picking)
- [ ] Inventory CRUD + locations
- [ ] Orders CRUD + status flow
- [ ] Picker sessions + rota + events
- [ ] Sync preview + apply (com mocks)
- [ ] Audit log completo + revert básico
- [ ] Jobs com progress tracking
- [ ] UI Web funcional
- [ ] Extension funcional (picking)
- [ ] 50+ testes passando
- [ ] docker compose up funciona
- [ ] Documentação atualizada
