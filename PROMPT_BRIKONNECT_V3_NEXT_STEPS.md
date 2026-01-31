# Brikonnect — Próximos Passos de Implementação (v3)

> **Para o Agente Codex:** Este documento contém as funcionalidades a implementar APÓS o M1-M6 estar completo. Segue a ordem indicada.

---

## Pré-requisitos

Antes de começar, valida que a implementação anterior funciona:

```bash
# 1. Setup
cp .env.example .env
docker compose up --build -d

# 2. Migrations + Seed
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed

# 3. Testes
docker compose exec api pytest -v

# 4. Verificar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

Se tudo passar, prossegue com as implementações abaixo.

---

## FASE 1: Billing System (Prioridade Alta)

### 1.1 Modelo de Dados

Criar migration `0007_billing.py`:

```sql
-- Histórico de versão do tenant (para billing pro-rata)
CREATE TYPE product_version AS ENUM ('lite', 'full');

CREATE TABLE tenant_version_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    version product_version NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    changed_by UUID REFERENCES users(id),
    change_reason VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_tenant_version_tenant ON tenant_version_history(tenant_id);
CREATE INDEX idx_tenant_version_active ON tenant_version_history(tenant_id) WHERE ended_at IS NULL;

-- Adicionar campos ao tenants
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS current_version product_version DEFAULT 'full';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS has_brikick_store BOOLEAN DEFAULT false;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_currency VARCHAR(3) DEFAULT 'EUR';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_email VARCHAR(320);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS paypal_payer_id VARCHAR(100);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    
    currency VARCHAR(3) NOT NULL,
    net_gmv NUMERIC(12,2) NOT NULL,
    
    lite_days INTEGER DEFAULT 0,
    lite_gmv NUMERIC(12,2) DEFAULT 0,
    lite_fee NUMERIC(10,2) DEFAULT 0,
    
    full_days INTEGER DEFAULT 0,
    full_gmv NUMERIC(12,2) DEFAULT 0,
    full_fee NUMERIC(10,2) DEFAULT 0,
    
    brikick_discount_applied BOOLEAN DEFAULT false,
    
    subtotal NUMERIC(10,2) NOT NULL,
    accumulated_from_previous NUMERIC(10,2) DEFAULT 0,
    total_due NUMERIC(10,2) NOT NULL,
    
    minimum_threshold NUMERIC(10,2) NOT NULL,
    below_minimum BOOLEAN DEFAULT false,
    
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    issued_at TIMESTAMPTZ,
    due_date DATE,
    paid_at TIMESTAMPTZ,
    
    payment_method VARCHAR(20),
    payment_reference VARCHAR(100),
    
    store_breakdown JSONB,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(tenant_id, year_month)
);
CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due ON invoices(due_date) WHERE status = 'ISSUED';

-- Payments
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    method VARCHAR(20) NOT NULL,
    
    stripe_payment_intent_id VARCHAR(100),
    stripe_charge_id VARCHAR(100),
    paypal_order_id VARCHAR(100),
    paypal_capture_id VARCHAR(100),
    
    status VARCHAR(20) NOT NULL,
    
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20),
    
    error_message TEXT,
    
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);

-- Payment Methods (saved for recurring)
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    method_type VARCHAR(20) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    
    stripe_customer_id VARCHAR(100),
    stripe_payment_method_id VARCHAR(100),
    
    paypal_payer_id VARCHAR(100),
    
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    
    paypal_email VARCHAR(320),
    
    created_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(tenant_id, stripe_payment_method_id),
    UNIQUE(tenant_id, paypal_payer_id)
);

-- Accumulated balance (for below-minimum months)
CREATE TABLE billing_accumulated (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 1.2 Módulo Backend

Criar `apps/api/app/modules/billing/`:

```
billing/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas
├── service.py     # Business logic (GMV calculation, invoice generation)
├── router.py      # API endpoints
├── deps.py        # Dependencies
├── stripe.py      # Stripe integration
└── paypal.py      # PayPal integration
```

**Endpoints a implementar:**

```python
# router.py
router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/status")
# Retorna: current_version, has_brikick_discount, current_rate, 
#          billing_status, current_month_gmv, current_month_estimated_fee

@router.post("/version")
# Body: { version: "lite" | "full" }
# Muda versão e regista em tenant_version_history

@router.get("/invoices")
# Lista invoices do tenant

@router.get("/invoices/{invoice_id}")
# Detalhe de uma invoice

@router.get("/invoices/{invoice_id}/pdf")
# Gera PDF da invoice

@router.post("/invoices/{invoice_id}/pay")
# Body: { method: "stripe" | "paypal", payment_method_id?: string }
# Processa pagamento

@router.get("/payment-methods")
# Lista métodos de pagamento guardados

@router.post("/payment-methods")
# Adiciona novo método de pagamento

@router.delete("/payment-methods/{id}")
# Remove método de pagamento

@router.post("/payment-methods/{id}/set-default")
# Define como default
```

**Taxas:**

```python
# service.py
RATES = {
    "lite": Decimal("0.01"),        # 1%
    "full": Decimal("0.025"),       # 2.5%
    "full_brikick": Decimal("0.02") # 2% com Brikick
}

MINIMUMS = {
    "EUR": Decimal("10.00"),
    "USD": Decimal("5.00"),
    "GBP": Decimal("8.00")
}
```

**Jobs a implementar:**

```python
# jobs/billing.py

async def generate_monthly_invoices():
    """
    Corre dia 1 de cada mês às 00:05 UTC.
    Gera invoices para todos os tenants activos.
    """
    pass

async def check_overdue_invoices():
    """
    Corre diariamente às 00:10 UTC.
    Suspende tenants com invoices vencidas (após dia 5).
    """
    pass

async def send_invoice_reminders():
    """
    Corre dia 3 e dia 4 de cada mês.
    Envia lembretes de pagamento.
    """
    pass
```

### 1.3 Frontend

Criar páginas em `apps/web/src/routes/`:

- `BillingPage.tsx` — Dashboard de billing (status, GMV actual, versão)
- `InvoicesPage.tsx` — Lista de invoices
- `InvoiceDetailPage.tsx` — Detalhe + botão pagar
- `PaymentMethodsPage.tsx` — Gerir métodos de pagamento

Adicionar à navegação em `Layout.tsx`.

### 1.4 Integração Stripe

```typescript
// Usar @stripe/stripe-js no frontend
// Checkout flow:
// 1. POST /billing/invoices/{id}/pay → backend cria PaymentIntent
// 2. Frontend usa Stripe Elements para confirmar pagamento
// 3. Webhook /webhooks/stripe confirma e atualiza invoice
```

### 1.5 Integração PayPal

```typescript
// Usar @paypal/react-paypal-js no frontend
// Checkout flow:
// 1. Frontend renderiza PayPal button
// 2. createOrder → POST /billing/invoices/{id}/pay?method=paypal
// 3. onApprove → POST /billing/payments/paypal/capture
```

### 1.6 Testes

Criar `tests/test_billing.py`:

- test_gmv_calculation
- test_prorata_version_change
- test_minimum_threshold_accumulation
- test_invoice_generation
- test_overdue_suspension

---

## FASE 2: Catalog Cache System (Prioridade Média)

### 2.1 Modelo de Dados

Criar migration `0008_catalog.py`:

```sql
-- Catalog Items (cache crescente)
CREATE TABLE catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_type VARCHAR(20) NOT NULL,
    item_no VARCHAR(64) NOT NULL,
    name VARCHAR(500) NOT NULL,
    category_id INTEGER,
    category_name VARCHAR(200),
    weight_grams NUMERIC(10,2),
    dimensions JSONB,
    image_url TEXT,
    thumbnail_url TEXT,
    year_released INTEGER,
    year_ended INTEGER,
    alternate_nos TEXT[],
    source VARCHAR(20) NOT NULL,
    source_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(item_type, item_no)
);
CREATE INDEX idx_catalog_type_no ON catalog_items(item_type, item_no);
CREATE INDEX idx_catalog_name ON catalog_items USING gin(to_tsvector('english', name));

-- Catalog Colors
CREATE TABLE catalog_colors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rgb VARCHAR(6),
    brickowl_id INTEGER,
    rebrickable_id INTEGER,
    ldraw_id INTEGER,
    lego_ids INTEGER[],
    color_type VARCHAR(20),
    source VARCHAR(20) DEFAULT 'bricklink',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Catalog Categories
CREATE TABLE catalog_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    parent_id INTEGER REFERENCES catalog_categories(id),
    source VARCHAR(20) DEFAULT 'bricklink',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ID Mappings (multi-platform)
CREATE TABLE catalog_id_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_type VARCHAR(20) NOT NULL,
    canonical_item_no VARCHAR(64) NOT NULL,
    bricklink_id VARCHAR(64),
    brickowl_id VARCHAR(64),
    brikick_id VARCHAR(64),
    rebrickable_id VARCHAR(64),
    lego_element_ids TEXT[],
    mapping_source VARCHAR(20),
    confidence NUMERIC(3,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(item_type, canonical_item_no)
);
CREATE INDEX idx_mapping_bricklink ON catalog_id_mappings(bricklink_id);
CREATE INDEX idx_mapping_brickowl ON catalog_id_mappings(brickowl_id);
CREATE INDEX idx_mapping_brikick ON catalog_id_mappings(brikick_id);
CREATE INDEX idx_mapping_rebrickable ON catalog_id_mappings(rebrickable_id);

-- Item-Color availability
CREATE TABLE catalog_item_colors (
    item_type VARCHAR(20) NOT NULL,
    item_no VARCHAR(64) NOT NULL,
    color_id INTEGER NOT NULL REFERENCES catalog_colors(id),
    qty_known INTEGER,
    source VARCHAR(20) DEFAULT 'bricklink',
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (item_type, item_no, color_id)
);

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

-- API Rate Limit Tracking
CREATE TABLE api_rate_limits (
    source VARCHAR(30) PRIMARY KEY,
    daily_limit INTEGER NOT NULL,
    requests_today INTEGER DEFAULT 0,
    last_request_at TIMESTAMPTZ,
    reset_at DATE,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 2.2 Módulo Backend

Criar `apps/api/app/modules/catalog/`:

```
catalog/
├── __init__.py
├── models.py
├── schemas.py
├── service.py      # Search logic, cache management
├── router.py
├── rebrickable.py  # Rebrickable API client
├── bricklink.py    # BrickLink API client (OAuth 1.0a)
└── importer.py     # Bulk import from dumps
```

**Endpoints:**

```python
@router.get("/search")
# Query params: q (text), item_type, platform_id
# Multi-reference search: procura por qualquer ID (BL/BO/Brikick/Rebrickable)

@router.get("/items/{item_type}/{item_no}")
# Detalhe de um item com todos os platform IDs

@router.get("/colors")
# Lista de cores com mappings

@router.get("/categories")
# Lista de categorias

@router.post("/import/colors")
# Admin: importar cores de dump

@router.post("/import/categories")
# Admin: importar categorias de dump

@router.post("/import/items")
# Admin: importar items de dump (CSV/JSON)
```

**Search Logic:**

```python
async def search_item(query: str) -> list[CatalogItem]:
    """
    1. Verifica se query é ID (numérico ou pattern conhecido)
    2. Se ID: procura em catalog_id_mappings por qualquer coluna
    3. Se texto: full-text search em catalog_items.name
    4. Se não encontrar localmente: query APIs externas
    5. Cache resultado
    """
    pass
```

### 2.3 Jobs

```python
# jobs/catalog.py

async def import_bricklink_dumps():
    """
    Corre semanalmente.
    Importa dumps de cores, categorias, items do BrickLink.
    """
    pass

async def sync_rebrickable_mappings():
    """
    Corre diariamente.
    Sincroniza cross-references do Rebrickable.
    """
    pass

async def refresh_stale_items():
    """
    Corre diariamente.
    Atualiza items com updated_at > 30 dias.
    """
    pass
```

### 2.4 Testes

- test_multi_reference_search
- test_cache_hit
- test_api_fallback
- test_rate_limit_tracking

---

## FASE 3: Brickognize Integration (Prioridade Média)

### 3.1 Modelo de Dados

Criar migration `0009_brickognize.py`:

```sql
-- Brickognize cache
CREATE TABLE brickognize_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_hash VARCHAR(64) NOT NULL UNIQUE,
    predictions JSONB NOT NULL,
    top_prediction_item_no VARCHAR(64),
    top_prediction_confidence NUMERIC(4,3),
    matched_catalog_item_id UUID REFERENCES catalog_items(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_brickognize_hash ON brickognize_cache(image_hash);
```

### 3.2 Backend

Criar `apps/api/app/modules/brickognize/`:

```python
# service.py
import hashlib
import httpx

BRICKOGNIZE_API = "https://api.brickognize.com/predict/"

async def identify_part(image_bytes: bytes) -> BrickognizeResult:
    """
    1. Calcular SHA256 da imagem
    2. Verificar cache
    3. Se não cached: chamar API Brickognize
    4. Mapear resultados para catalog local
    5. Guardar em cache
    6. Retornar predictions com platform IDs
    """
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    
    # Check cache
    cached = await get_cached_prediction(image_hash)
    if cached:
        return cached
    
    # Call Brickognize API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            BRICKOGNIZE_API,
            files={"image": image_bytes}
        )
        data = response.json()
    
    # Map to local catalog
    predictions = []
    for item in data.get("items", []):
        catalog_item = await get_catalog_item(item["id"])
        predictions.append({
            "item_no": item["id"],
            "name": item.get("name"),
            "confidence": item.get("score", 0),
            "image_url": item.get("img_url"),
            "platform_ids": await get_platform_ids(item["id"])
        })
    
    # Cache result
    await cache_prediction(image_hash, predictions)
    
    return BrickognizeResult(predictions=predictions)

# router.py
@router.post("/identify")
async def identify_part(
    image: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """Identify LEGO part from image."""
    image_bytes = await image.read()
    result = await brickognize_service.identify_part(image_bytes)
    return result

@router.post("/search/image")
async def search_by_image(
    image: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """Search inventory by image."""
    # Identify part
    result = await brickognize_service.identify_part(await image.read())
    
    # Search in tenant's inventory
    if result.predictions:
        top_item = result.predictions[0]
        inventory_matches = await inventory_service.search(
            tenant_id=current_user.tenant_id,
            item_no=top_item["item_no"]
        )
        result.inventory_matches = inventory_matches
    
    return result
```

### 3.3 Frontend

Adicionar a `InventoryPage.tsx` e pesquisa global:

```tsx
// components/BrickognizeButton.tsx
export function BrickognizeButton({ onResult }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleCapture = async (file: File) => {
    const formData = new FormData();
    formData.append('image', file);
    
    const result = await api.post('/brickognize/identify', formData);
    onResult(result.predictions);
  };
  
  return (
    <>
      <Button onClick={() => fileInputRef.current?.click()}>
        <Camera className="w-4 h-4 mr-2" />
        Identify Part
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleCapture(e.target.files[0])}
      />
    </>
  );
}

// Usar em AddInventoryDialog e SearchBar
```

### 3.4 Extension

Adicionar à extensão `sidepanel/`:

```tsx
// Botão de câmara para quick identify
// Usa navigator.mediaDevices.getUserMedia() se disponível
// Fallback para file input
```

### 3.5 Testes

- test_identify_caches_result
- test_identify_maps_to_catalog
- test_search_by_image

---

## FASE 4: Shipping Carriers (Prioridade Média)

### 4.1 Modelo de Dados

Já existe em migration anterior. Verificar e expandir se necessário.

### 4.2 Backend

Criar adapters em `apps/api/app/integrations/shipping/`:

```
shipping/
├── __init__.py
├── base.py         # ShippingAdapter protocol
├── sendcloud.py
├── shipstation.py
├── pirateship.py
├── dhl.py
├── postnl.py
└── registry.py     # Carrier registry
```

**Interface comum:**

```python
# base.py
from typing import Protocol

class ShippingAdapter(Protocol):
    async def get_rates(
        self, 
        package: Package, 
        origin: Address,
        destination: Address
    ) -> list[ShippingRate]:
        ...
    
    async def create_label(
        self, 
        shipment: ShipmentRequest
    ) -> LabelResponse:
        ...
    
    async def track(
        self, 
        tracking_number: str
    ) -> TrackingInfo:
        ...
    
    async def cancel(
        self, 
        shipment_id: str
    ) -> bool:
        ...
```

**Implementar pelo menos 2-3 carriers reais:**

1. SendCloud (EU) — mais comum para sellers europeus
2. ShipStation (global) — aggregator popular
3. PirateShip (US) — popular para US sellers

### 4.3 Módulo

Criar `apps/api/app/modules/shipping/`:

```python
# router.py
@router.get("/carriers")
# Lista carriers configurados pelo tenant

@router.post("/carriers")
# Adiciona/configura carrier

@router.post("/rates")
# Body: { order_id, carrier_codes[] }
# Obtém rates de múltiplos carriers

@router.post("/labels")
# Body: { order_id, carrier_code, service_level }
# Cria label (async job)

@router.get("/labels/{shipment_id}")
# Detalhe + download label

@router.get("/track/{tracking_number}")
# Tracking info

@router.post("/labels/{shipment_id}/cancel")
# Cancela shipment
```

### 4.4 Frontend

- `ShippingCarriersPage.tsx` — Configurar carriers
- Adicionar a `OrderDetailPage.tsx` — Botão "Create Shipping Label"
- `CreateLabelDialog.tsx` — Selecionar carrier, ver rates, criar label

### 4.5 Testes

- test_get_rates_multiple_carriers
- test_create_label
- test_track_shipment

---

## FASE 5: Email System (Prioridade Média)

### 5.1 Modelo de Dados

Criar migration `0010_email.py`:

```sql
-- Email Templates
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    template_key VARCHAR(50) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    variables JSONB DEFAULT '[]',
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
    status VARCHAR(20) DEFAULT 'PENDING',
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    template_key VARCHAR(50),
    reference_type VARCHAR(50),
    reference_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_email_queue_pending ON email_queue(status) WHERE status = 'PENDING';

-- Notifications (in-app)
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT,
    action_url TEXT,
    action_label VARCHAR(50),
    reference_type VARCHAR(50),
    reference_id UUID,
    read_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_notifications_user ON notifications(tenant_id, user_id, read_at);
```

### 5.2 Backend

Criar `apps/api/app/modules/email/`:

```python
# service.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None
    ) -> bool:
        """Send email via SMTP."""
        pass
    
    async def send_template(
        self,
        to: str,
        template_key: str,
        variables: dict,
        tenant_id: UUID | None = None
    ) -> bool:
        """Send email using template."""
        pass
    
    async def queue_email(
        self,
        to: str,
        template_key: str,
        variables: dict,
        tenant_id: UUID | None = None
    ) -> UUID:
        """Queue email for async sending."""
        pass

# Templates padrão:
SYSTEM_TEMPLATES = {
    "welcome": {
        "subject": "Welcome to Brikonnect!",
        "variables": ["user_name", "tenant_name", "login_url"]
    },
    "password_reset": {
        "subject": "Reset your password",
        "variables": ["user_name", "reset_url", "expires_in"]
    },
    "order_shipped": {
        "subject": "Your order has shipped - {order_no}",
        "variables": ["buyer_name", "order_no", "tracking_number", "tracking_url"]
    },
    "invoice_issued": {
        "subject": "Your Brikonnect invoice for {month}",
        "variables": ["tenant_name", "month", "amount", "due_date", "pay_url"]
    },
    "invoice_overdue": {
        "subject": "Payment overdue - Action required",
        "variables": ["tenant_name", "amount", "pay_url"]
    },
    "sync_completed": {
        "subject": "Sync completed successfully",
        "variables": ["sync_type", "items_updated", "items_added", "items_removed"]
    },
    "sync_failed": {
        "subject": "Sync failed - Action required",
        "variables": ["sync_type", "error_message"]
    }
}
```

### 5.3 Jobs

```python
# jobs/email.py

async def process_email_queue():
    """
    Corre a cada minuto.
    Processa emails pendentes na queue.
    """
    pending = await get_pending_emails(limit=50)
    for email in pending:
        try:
            await email_service.send(
                to=email.to_email,
                subject=email.subject,
                body_html=email.body_html,
                body_text=email.body_text
            )
            email.status = "SENT"
            email.sent_at = datetime.utcnow()
        except Exception as e:
            email.attempts += 1
            email.last_attempt_at = datetime.utcnow()
            email.error_message = str(e)
            if email.attempts >= 3:
                email.status = "FAILED"
        await save(email)
```

### 5.4 Notifications Module

Criar `apps/api/app/modules/notifications/`:

```python
# router.py
@router.get("/")
# Lista notificações do user

@router.post("/{id}/read")
# Marca como lida

@router.post("/read-all")
# Marca todas como lidas

@router.post("/{id}/dismiss")
# Descarta notificação
```

### 5.5 Frontend

- `NotificationsDropdown.tsx` — Bell icon no header com badge
- Adicionar badge count via polling ou WebSocket

### 5.6 Extension

- Badge no ícone da extensão com count de notificações
- `chrome.action.setBadgeText()`

---

## FASE 6: Polish & Production (Prioridade Alta antes de Launch)

### 6.1 Dark Mode Toggle

Já existe suporte. Implementar toggle funcional:

```tsx
// components/ThemeToggle.tsx
export function ThemeToggle() {
  const [theme, setTheme] = useLocalStorage('theme', 'system');
  
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark' || 
        (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => setTheme('light')}>Light</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>Dark</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>System</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

### 6.2 Error Handling

Criar error boundary e toast notifications consistentes:

```tsx
// components/ErrorBoundary.tsx
// lib/error-handler.ts — Centralizar tratamento de erros API
```

### 6.3 Loading States

Adicionar skeletons a todas as páginas:

```tsx
// components/Skeleton.tsx
// Usar em todas as queries com isLoading
```

### 6.4 Mobile Responsive

Verificar e corrigir layouts em mobile:
- Sidebar colapsável
- Tabelas com scroll horizontal
- Forms adaptados

### 6.5 Rate Limiting

Adicionar rate limiting à API:

```python
# middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Em endpoints sensíveis:
@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
    pass
```

### 6.6 Logging Estruturado

Adicionar correlation_id a todos os logs:

```python
# middleware/logging.py
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id.set(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response
```

### 6.7 Sentry Integration

```python
# main.py
import sentry_sdk

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT
    )
```

### 6.8 CI/CD Pipeline

Atualizar `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
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
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          cd apps/api
          pytest -v --cov=app
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret
          JWT_SECRET_KEY: test-jwt-secret
          ENCRYPTION_KEY: test-encryption-key
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push Docker images
        run: |
          docker compose build
          # Push to registry...
```

### 6.9 Traefik para Produção

Criar `docker-compose.prod.yml`:

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v3.0
    command:
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
    networks:
      - brikonnect

  api:
    # ... same as before
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.brikonnect.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"

  web:
    # ... same as before
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=HostRegexp(`{tenant:[a-z0-9-]+}.brikonnect.com`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"

volumes:
  traefik_certs:

networks:
  brikonnect:
```

---

## Checklist Final

Antes de considerar pronto para produção:

- [ ] Billing funcional com Stripe e PayPal
- [ ] Catalog cache a funcionar
- [ ] Brickognize integrado
- [ ] Pelo menos 2 shipping carriers reais
- [ ] Email system funcional
- [ ] Dark mode toggle
- [ ] Error handling consistente
- [ ] Loading states em todas as páginas
- [ ] Mobile responsive
- [ ] Rate limiting activo
- [ ] Logging com correlation_id
- [ ] Sentry configurado
- [ ] CI/CD a passar
- [ ] docker compose up --build funciona
- [ ] Testes > 80% coverage
- [ ] Documentação actualizada

---

## Ordem de Implementação Sugerida

1. **Billing** (crítico para monetização)
2. **Email** (necessário para billing notifications)
3. **Catalog Cache** (melhora UX significativamente)
4. **Brickognize** (diferenciador)
5. **Shipping Carriers** (pelo menos mocks funcionais)
6. **Polish & Production** (antes de launch)

**Tempo estimado:** 2-4 semanas para implementação completa.
