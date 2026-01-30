# Compilação — Brikonnect (site público) + Demo UI (tenant app)

## 1) Duas superfícies / dois codebases

### A) Site público (`brikonnect.com`) — marketing + docs
- Stack inferida (do ZIP anterior): **Nuxt 3 (Vue 3) + Vite + @nuxt/content (document-driven)**.
- Conteúdo em páginas como `/guides/*`, `/news/*`, `/integrations/*`.
- Conteúdo dinâmico via `public.content.api.baseURL = "/api/_content"` (Nuxt Content).

### B) App por tenant (`*.brikonnect.com`) — produto real
- Stack inferida (do demo ZIP): **Vue 2 + VueRouter + Vuex + Webpack (code-splitting)**.
- HTML injecta `window.BRIKONNECT_STATE` e carrega bundles via CDN `cdn.brikonnect.com/static/dist/js/*`.
- Rotas “core” confirmadas pelo manifest: `/inventory/`, `/orders/`, `/picker/`.
- Consome backend via **same-origin**: `/api/v1/*` com trailing slash.

---

## 2) Alinhamento entre UI e documentação de API

O que o demo UI comprova:
- A plataforma funciona com um backend REST em `/api/v1/`.
- Existe autenticação por password + WebAuthn, e tenant config centralizada (`/api/v1/tenant/...`).

O que o site público (docs) acrescenta:
- lista de domínios de API que o produto completo expõe, incluindo:
  - `/api/v1/inventory/`
  - `/api/v1/orders/`
  - `/api/v1/shipments/`
  - `/api/v1/shipping/`
  - `/api/v1/invoices/`, `/api/v1/payouts/`, `/api/v1/shops/`, `/api/v1/definitions/`, etc.

Isto coincide com o manifest (Inventory/Orders/Picker) e com o guard `inventory.dashboard` observado no router.

---

## 3) O “/v1/API” que referiste

Nos dois artefactos:
- o padrão observável é **`/api/v1/...`**.
- não foi encontrado um diretório literal `/v1/API` dentro dos ZIPs; quando aparece “v1” é como parte do path REST.

Se estás a ver referências a “/v1/API” noutros ficheiros/HARs, é provável que:
- seja apenas um alias/rewriter do reverse proxy, ou
- seja um prefixo interno (ex.: gateway) não exposto no shell público.

---

## 4) O que falta para o demo UI ser “funcional”

O demo ZIP contém apenas:
- `login_entry` + `chunk-common` + `chunk-vendors`
- manifest e logs HTTrack

Mas o `chunk-common` referencia **76 chunks dinâmicos ausentes** (páginas reais). Portanto, para teres a UI completa como base de arranque tens duas vias:

### Via 1 — Recuperar os chunks ausentes
- Capturar todos os `chunk-*.js` carregados no browser (Network) enquanto navegas no demo/tenant (com credenciais válidas).
- Guardar a árvore `static/dist/js/` completa.

### Via 2 — Usar isto como “spec” e recriar as páginas
- Manténs a estrutura:
  - router history mode
  - splitview + sidebar menu via `meta.menuComponent`
  - RBAC via `meta.allowedRoles`
  - endpoints `/api/v1/*`
- Recrias as páginas Inventory/Orders/Picker com UI tua (o que encaixa com o teu objetivo).

---

## 5) Reutilização direta no teu projeto (Brikonnect) — compilação com a conversa

Com base no que já definimos para o Brikonnect:
- queres **marketplace** (BrickLink-alike) com backend robusto e um frontend moderno.
- os artefactos Brikonnect são úteis como referência de:
  - **arquitetura multi-tenant**
  - **modularização por domínio** (inventory/orders/shipping/billing)
  - **RBAC + route meta**
  - **PWA + shortcuts** para fluxos core
  - **WebAuthn** como upgrade de segurança/UX (opcional)

Tradução para Brikonnect (sugestão técnica compatível com o que já decidiste):
- manter `api/v1` como prefixo dos teus endpoints (em FastAPI)
- estruturar domínios semelhantes: `inventory`, `orders`, `shipments`, `shipping`, `billing`, `notifications`, `definitions`
- implementar “tenant bootstrap” (equivalente ao `window.BRIKONNECT_STATE`) via:
  - endpoint `GET /api/v1/tenant/bootstrap` ou
  - SSR no HTML da app (se mantiveres Vue para esta parte)

---

## 6) Próximo passo objetivo (sem depender de adivinhações)

- Se o teu objetivo é “tornar funcional” com backend próprio, o passo certo é:
  1) **Definir um contrato mínimo** (OpenAPI) para:
     - login + sessão
     - bootstrap tenant
     - inventory search
     - orders list + details
     - picker workflow
  2) Implementar stubs no backend (FastAPI) e ligar o Vue router/pages a esses endpoints.
  3) Iterar módulo a módulo.

(Para isto, o demo ZIP já te dá o contrato exato dos endpoints de login e WebAuthn.)
