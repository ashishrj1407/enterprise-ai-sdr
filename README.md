# Customer Architecture POC

Small, runnable demo of **customer-specific customization** for the AI SDR stack (FastAPI + MySQL + Next.js + Celery), following:

- `explore/ARCHITECTURE_FINALIZATION_README.md`
- `explore/AI_SDR_TWO_CUSTOMER_ARCHITECTURE_PRESENTATION.md`
- `plan-poc.md`

**Full architecture (explain / adapt for developers):** [ARCHITECTURE_README.md](./ARCHITECTURE_README.md)

| Deep dive | Doc |
|---|---|
| Frontend base-first | [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md) |
| Backend base-first | [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md) |
| Database + Alembic | [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) |
| DB bootstrap / migration runbooks | [db/README.md](./db/README.md) · [backend/migrations/README.md](./backend/migrations/README.md) |
| Celery + Redis jobs | [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md) · [backend/JOBS.md](./backend/JOBS.md) |

## What this demonstrates

```text
                    Base Product
                 /               \
                /                 \
       Customer A              Customer B
       (customer-1)            (customer-2)
       /        \              /        \
   Frontend   Backend      Frontend   Backend
```

| Concern | Base product | Customer A (`customer-1`) | Customer B (`customer-2`) | Customer C (`customer-3`) |
|---|---|---|---|---|
| Identity | Tenant resolver + catalog | GreenGrid Solar | FinTrust Loans | BaseCo (base only) |
| Frontend | Shared lead fields | + roof size, energy bill | + consent, product type | No extras |
| API | `POST /api/base-endpoint1` → **string** | `POST /api/customer-1-endpoint` → **integer** | `POST /api/customer-2-endpoint` → **percentage** | Uses base endpoint |
| Database | Shared `generic.tenants` | `schema_customer_1` | `schema_customer_2` | `schema_customer_3` |

Core product code is **not** forked per customer. Customer behaviour lives in dedicated folders and is discovered via an extension registry / config loader.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Optional for local tests: Python 3.12+, Node.js 20+

## Start the application

```bash
cd customer-architecture-poc
docker compose up --build
```

First boot:

1. MySQL bootstrap — empty `generic` + `schema_customer_*` + grants (`db/init`)
2–5. Alembic via backend — platform → base → customer → seed
6. Deploy API, then **Celery worker + beat** (Redis), then frontend

(may take ~30–60s on a fresh volume)

### URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| Backend health | http://localhost:8000/api/health |
| Jobs schedule | http://localhost:8000/api/jobs/schedule |
| Job runs | http://localhost:8000/api/jobs/runs |
| MySQL | `localhost:3307` (user `poc` / password `pocpass`) |
| Redis | `localhost:6379` |

**Celery + Redis jobs** (detail): [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md) · [backend/JOBS.md](./backend/JOBS.md)  
**Whole POC architecture:** [ARCHITECTURE_README.md](./ARCHITECTURE_README.md)

### Database install sequence

| Step | What | Where |
|---|---|---|
| 1 Bootstrap | Empty DBs + GRANTs (no tables) | `db/init/01_schemas.sql` |
| 2 Platform | Tables in `generic` (`tenants`, `job_runs`, …) | `backend/migrations/platform` |
| 3 Base | Shared tables → every tenant schema | `backend/migrations/base` |
| 4 Customer | Extras → one schema | `app/customers/*/migrations` |
| 5 Seed | Catalog + demo leads if empty | `migrate_all` |
| 6 Deploy | Backend then frontend | Compose |

Details: [db/README.md](./db/README.md) · [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) · [backend/migrations/README.md](./backend/migrations/README.md)

| Schema | Purpose |
|---|---|
| `generic` | Shared tenant catalog (`tenants`) — not customer lead data |
| `schema_customer_1` | Customer A leads (+ solar columns via customer Alembic) |
| `schema_customer_2` | Customer B leads (+ consent columns via customer Alembic) |
| `schema_customer_3` | Customer C leads (base columns only) |

## How to select / run a specific customer

### Demo UI (easiest)

Open http://localhost:3000 and use the **Active customer** dropdown.

The UI loads `frontend/app/customers/<id>/config.js`, which decides:

- extra form fields
- which API endpoint to call
- expected result type

Every request sends `X-Customer-Id` so the backend resolves the correct tenant and schema.

### API / curl

```bash
# Customer A — integer solar-fit score
curl -s -X POST http://localhost:8000/api/customer-1-endpoint \
  -H 'Content-Type: application/json' \
  -H 'X-Customer-Id: customer-1' \
  -d '{"name":"Alex","email":"alex@example.com","roof_size_sqft":500,"monthly_energy_bill":120}'

# Customer B — compliance percentage
curl -s -X POST http://localhost:8000/api/customer-2-endpoint \
  -H 'Content-Type: application/json' \
  -H 'X-Customer-Id: customer-2' \
  -d '{"name":"Blair","email":"blair@example.com","consent_given":true,"product_type":"term_loan"}'

# Customer C — base string qualification
curl -s -X POST http://localhost:8000/api/base-endpoint1 \
  -H 'Content-Type: application/json' \
  -H 'X-Customer-Id: customer-3' \
  -d '{"name":"Casey","email":"casey@example.com","company":"BaseCo"}'
```

Host-based resolution is also supported (`customer-1.localhost`, etc.) via the same pattern as `AI-SDR-Enterprise-Frontend/app/api/_lib/backendResolver.js`.

## Folder structure

```text
customer-architecture-poc/
├── docker-compose.yml
├── db/
│   ├── README.md                 # Step 1 bootstrap only
│   └── init/01_schemas.sql       # empty DBs + GRANTs (no tables)
├── backend/
│   ├── migrations/               # Steps 2–3 (platform + base) + migrate_all docs
│   ├── docker-entrypoint.sh      # api | worker | beat
│   ├── JOBS.md                   # Celery + Redis vs ElevenLabs APScheduler
│   └── app/
│       ├── core/                 # BASE API (resolver, tenant, registry, celery_app)
│       ├── jobs/                 # Celery tasks + /api/jobs routes + tracking
│       ├── domains/leads/
│       └── customers/            # CUSTOMER-SPECIFIC API + optional migrations/jobs
└── frontend/
    └── app/
        ├── page.js               # Thin orchestrator (no customer logic)
        ├── core/                 # BASE FRONTEND (complete default implementation)
        │   ├── components/       # Hero, LeadForm, FieldRow, LeadList, …

        │   ├── layouts/          # AppShell
        │   ├── hooks/            # useLeadQualification
        │   ├── theme.js
        │   ├── baseFields.js
        │   ├── composeFields.js
        │   └── resolveFrontend.js  # customer override + base fallback
        └── customers/            # CUSTOMER OVERRIDES ONLY
            ├── customer-1/
            │   ├── index.js      # exports config + components map
            │   ├── config.js     # fieldPlan / theme
            │   └── components/   # optional slot overrides (LeadForm, …)
            ├── customer-2/       # config only → full base UI fallback
            └── customer-3/       # config only → full base UI fallback
```

## How customer-specific customization works

1. **Resolver** establishes an immutable tenant context from `X-Customer-Id` (or host map).
2. **Extension registry** discovers `backend/app/customers/*/manifest.json` and mounts any customer routers.
3. **Frontend resolver** (`resolveFrontend`) loads the customer package and merges config + component slots.
4. **Schema routing** uses `USE schema_customer_N` so leads never cross tenants.
5. **Isolation checks** reject calling another customer’s endpoint with the wrong tenant header (HTTP 403).

## Frontend architecture: base-first, customer override

Principles enforced by `resolveFrontend`:

| Principle | Implementation |
|---|---|
| Base-first | Complete UI lives under `frontend/app/core/` |
| Customer override | Customer package `components.<Slot>` replaces that slot |
| Fallback | Missing customer slot → base component automatically |
| Extensible | New customer = new folder + one registry line; no base edits |
| Portable | Base has no imports from `customers/` |
| Maintainable | Only deltas live in customer folders |
| Clear separation | `core/` = product, `customers/<id>/` = overrides |

```text
resolveFrontend(customerId)
        │
        ├─ config:  customer fieldPlan/theme  >  BASE_FIELDS / BASE_THEME
        └─ slots:   customer components.LeadForm?  else  core/components/LeadForm
```

Overridable slots: `AppShell`, `Hero`, `CustomerPanel`, `LeadForm`, `LeadList`, `ArchitecturePanel`.

### Config preference (fields / theme)

| Need | How |
|---|---|
| Reorder fields | `fieldPlan.order` |
| Override a base field | `fieldPlan.overrides` (customer keys win) |
| Clear a base style | `overrides: { name: { style: null } }` |
| Add customer fields | `fieldPlan.extras` |
| Override a component | `components: { LeadForm: () => import("./components/LeadForm") }` |
| Use base UI only | export `components: {}` (customer-2 / customer-3) |

## How to add a new customer

Example: `customer-4`

### Backend

1. Create `backend/app/customers/customer_4/manifest.json`
2. Create `backend/app/customers/customer_4/__init__.py` with optional `router` and `HOOKS`
3. **Bootstrap:** add `schema_customer_4` + `GRANT` in `db/init/01_schemas.sql` (or ops equivalent), then apply on DB
4. Optional: `app/customers/customer_4/migrations/` for extras (after base)
5. Run `python -m app.core.migrate_all` (steps 2–5)
6. Deploy backend → frontend

No changes are required in `core/routes/base.py` for a dedicated customer endpoint.

### Frontend

1. Create `frontend/app/customers/customer-4/config.js`
2. Create `frontend/app/customers/customer-4/index.js` exporting `config` and optional `components`
3. Register one line in `frontend/app/customers/registry.js` → `CUSTOMER_PACKAGES`
4. Optionally add `components/LeadForm.js` (or any slot) to override base UI

No changes to `core/components` are required for customer-only behaviour.

## Tests

```bash
# Backend (resolver + customer behaviour + API isolation)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q

# Frontend resolver unit tests
cd frontend
npm install
npm test
```

## Stop and clean up

```bash
# Stop containers
docker compose down

# Stop and delete the MySQL volume (re-runs step 1 bootstrap on next up)
docker compose down -v
```

## Mapping back to plan-poc.md

| plan-poc.md | POC implementation |
|---|---|
| customer-1 extra field → `/customer-1-endpoint` | Solar fields → integer score |
| customer-2 → `/customer-2-endpoint` | Consent fields → percentage |
| customer-3 → `/base-endpoint1` | Base form only → string |
| Resolver | Host / `X-Customer-Id` resolver on FE + BE |
| schema-1 / schema-2 / schema-3 | `schema_customer_1` / `_2` / `_3` |

## Notes for team demos

- Emphasize that **Customer A code cannot affect Customer B** because routes, scoring, and schemas are folder-isolated and tenant-gated.
- Emphasize that **Customer C proves onboarding without custom code** — only a manifest + schema.
- Emphasize the upgrade path to the full architecture: versioned hooks, sandboxed plugin workers, signed manifests, and the bootstrap → Alembic (platform/base/customer) → deploy sequence.
