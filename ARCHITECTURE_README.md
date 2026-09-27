# Customer Architecture POC — Full Architecture Guide

**For developers:** this document explains the **entire architecture implemented in `customer-architecture-poc`**, so you can present it and adapt the same patterns into AI SDR / campaign products.

**Runnable entrypoint:** [README.md](./README.md)  
**Frontend deep dive:** [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)  
**Backend deep dive:** [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)  
**Database deep dive:** [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md)  
**DB migration runbook:** [backend/migrations/README.md](./backend/migrations/README.md)  
**Jobs (Celery):** [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md) · [backend/JOBS.md](./backend/JOBS.md)

---

## 1. What this POC proves

One **base product**, many **customers**, without forking the codebase.

```text
                         ┌──────────────────────────┐
                         │      Base product         │
                         │  FE core · BE core · DB   │
                         │  base · jobs (Celery)     │
                         └────────────┬─────────────┘
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
       customer-1              customer-2              customer-3
       GreenGrid Solar         FinTrust Loans          BaseCo (base only)
       FE overrides            config only             config only
       BE endpoint + cols      BE endpoint + cols      base endpoint
       job enrich              base jobs               base jobs
```

| Layer | Base | Customer override | Fallback |
|---|---|---|---|
| Frontend | `frontend/app/core/` | `frontend/app/customers/<id>/` | Missing slot → base |
| Backend API | `backend/app/core/`, `domains/` | `backend/app/customers/<id>/` | No router → base routes |
| Database | `migrations/base` on every tenant schema | `customers/<id>/migrations` | No extras → base tables only |
| Jobs | `backend/app/jobs/` | `customers/<id>/jobs.py` | No module → base task behaviour |
| Identity | Resolver + `generic.tenants` | Manifest / host / header | Default customer |

**Customer-3** is intentional: onboarding with **no custom code** (manifest + empty schema + base UI/API/jobs only).

---

## 2. System context (runtime)

```text
Browser / curl
    │
    ▼
┌──────────────┐     X-Customer-Id      ┌────────────────────────────┐
│  Next.js FE  │ ─────────────────────► │  FastAPI backend (API)     │
│  :3000       │   /api/backend/*       │  :8000                     │
└──────────────┘                        │  tenant resolver           │
                                        │  customer routers          │
                                        │  /api/jobs (observe/trigger)│
                                        └───────┬───────────┬────────┘
                                                │           │
                         USE schema_customer_N  │           │ enqueue
                                                ▼           ▼
                                        ┌──────────┐  ┌─────────┐
                                        │  MySQL   │  │  Redis  │
                                        │  :3307   │  │  :6379  │
                                        └──────────┘  └────┬────┘
                                              ▲            │
                                              │       queue│
                         job_runs + tenants   │            ▼
                                        ┌─────┴────┐  ┌────────────┐
                                        │  Worker  │◄─│ Celery Beat│
                                        └──────────┘  └────────────┘
```

### Compose services

| Service | Role |
|---|---|
| `db` | MySQL — platform DB `generic` + tenant schemas |
| `redis` | Celery broker / result backend |
| `backend` | FastAPI API only (no embedded cron) |
| `worker` | Celery workers |
| `beat` | Celery Beat scheduler |
| `frontend` | Next.js demo UI |

---

## 3. Core design rule (repeat this to the team)

> **Base implements the full product. Customer folders hold deltas only. Customer always wins when present; otherwise base is used.**

Same rule everywhere:

| Concern | Preference order |
|---|---|
| UI component / hook / CSS | customer package → base |
| Form fields / theme | customer `fieldPlan` → `BASE_FIELDS` / `BASE_THEME` |
| API behaviour | customer router / hooks → base routes |
| Table columns | customer Alembic (after base) → base table |
| Job payload enrichment | `customers/<id>/jobs.py` → base task |

Never fork `core/` per customer.

---

## 4. End-to-end request flow

### 4.1 Interactive lead qualification (UI → API → DB)

```text
1. User selects customer in UI (stored in localStorage)
2. resolveFrontend(customerId)
      → loads customers/registry.js package
      → merges config + component/hook slots (customer > base)
3. Form submit → POST /api/backend{endpoint}
      → proxy adds X-Customer-Id
4. Backend resolver → TenantContext (immutable)
5. Route:
      customer-1 → /customer-1-endpoint (integer score)
      customer-2 → /customer-2-endpoint (percentage)
      customer-3 → /base-endpoint1 (string)
6. Handler writes into that tenant’s schema only (USE schema_customer_N)
7. Isolation: wrong customer header on a foreign endpoint → 403
```

### 4.2 Background job flow (Beat → Worker → DB)

```text
1. Celery Beat fires lead_status_sync (schedule outside API)
2. Worker enqueues tenant_lead_status_sync(customer_id) per tenant
3. Each child:
      - starts row in generic.job_runs
      - reads that tenant’s leads
      - optional customers/<id>/jobs.enrich_status_sync
      - finishes job_runs success/failed
4. API can list history: GET /api/jobs/runs
```

This replaces in-process APScheduler (as in `AI_SDR_CampaignManagement-ElevenLabs`).

---

## 5. Identity & tenancy

### 5.1 Two “resolver” concepts (do not conflate)

| Name | Question it answers | Main code |
|---|---|---|
| **Tenant identity resolver** | Which customer is this request? | BE `resolver.py` / `tenant.py`; FE header + optional host map |
| **Frontend composition resolver** | Which UI/config wins for that customer? | `resolveFrontend.js` + `customers/registry.js` |

Customer folders do **not** replace identity resolution. They depend on a resolved `customerId`.

### 5.2 Resolution order (backend)

1. `X-Customer-Id` header (demo UI / curl)  
2. Host map (`customer-1.localhost` → `customer-1`)  
3. Default customer (`customer-3`)

### 5.3 Platform catalog DB: `generic`

`generic` is the **shared directory**, not lead data.

| Table | Purpose |
|---|---|
| `tenants` | customer_id → schema_name, endpoint, result_type, display_name |
| `job_runs` | durable Celery run history |

Lead/business tables live only in `schema_customer_*`.

---

## 6. Frontend architecture (summary)

Details: [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)

```text
page.jsx / info/page.jsx
        │
        ▼
resolveFrontend(customerId)
        │
        ├─ registry → customers/<id>/index.js
        ├─ config/theme merge (customer wins)
        └─ slots: AppShell, Hero, LeadForm, Styles, hooks, …
                 missing → frontend/app/core/*
```

| Customer | What is overridden |
|---|---|
| customer-1 | AppShell, LeadForm, Styles, InfoPage, BrandIcon, hook, fieldPlan |
| customer-2 | config / fields only → full base UI |
| customer-3 | config only → full base UI |

When switching customers, the UI waits until `resolved.customerId === activeCustomerId` so hooks/components remount safely (Rules of Hooks).

---

## 7. Backend architecture (summary)

Details: [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)

```text
app/main.py
  ├── core/routes/base.py          /health /me /base-endpoint1 /leads
  ├── jobs/routes.py               /jobs/schedule /jobs/runs /jobs/trigger/*
  └── customers/*/router           /customer-1-endpoint, /customer-2-endpoint, …

app/core/
  resolver.py + tenant.py          identity → TenantContext
  extension_registry.py            discover manifests, routers, HOOKS
  database.py                      tenant_session → USE schema
  migrate_all.py                   steps 2–5
  celery_app.py                    Beat schedule + Celery config

app/domains/leads/                 base qualify + list
app/customers/<id>/                manifest, router, HOOKS, migrations/, jobs.py
```

Isolation rules:

- Data access is schema-scoped per tenant  
- Customer-specific routes reject mismatched `X-Customer-Id`  
- Manifests describe endpoint / schema / extras for discovery and seeding  

---

## 8. Database & migration architecture (summary)

Details: [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) · runbook: [backend/migrations/README.md](./backend/migrations/README.md)

### 8.1 Install sequence (mandatory order)

```text
1. Bootstrap     db/init/01_schemas.sql     empty DBs + GRANTs (no tables)
2. Platform      migrations/platform        tables in `generic`
3. Base          migrations/base            fan-out to every schema_customer_*
4. Customer      customers/*/migrations     extras on one schema only
5. Seed          migrate_all                tenants + demo leads if empty
6. Deploy        API → Worker/Beat → FE
```

| Step | Creates tables? | Who runs it |
|---|---|---|
| 1 Bootstrap | No | MySQL init (root / ops) |
| 2–4 Alembic | Yes | `python -m app.core.migrate_all` |
| 5 Seed | Rows only | same orchestrator |
| 6 Deploy | — | Docker Compose |

### 8.2 Version tables

| Chain | Version table | Where |
|---|---|---|
| Platform | `alembic_version` | `generic` |
| Base | `alembic_version_base` | each tenant schema |
| Customer | `alembic_version_customer` | each tenant schema that has overrides |

### 8.3 Conflict rules

- Base owns shared columns (`name`, `email`, `company`, `address`, …)  
- Customer migrations only **ADD** customer columns / tables  
- Customer chain runs only after required base revision is applied  
- Do not edit applied migration files; append new revisions  

Bootstrap vs Alembic:

```text
01_schemas.sql  →  empty rooms + keys for app user
Alembic         →  furniture (tables/columns) inside rooms
```

---

## 9. Jobs architecture (Celery + Redis)

Full adaptation guide for ElevenLabs: [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md)

| Before (typical legacy) | In this POC |
|---|---|
| APScheduler inside uvicorn | Celery Beat process |
| `UVICORN_WORKERS=1` forced | API scalable independently |
| Log-only tracking | `generic.job_runs` |
| Giant multi-tenant loop | Fan-out: one parent + per-tenant children |

Demo jobs:

| Beat entry | Meaning |
|---|---|
| `lead-status-sync` | Fan-out status tick per tenant |
| `platform-heartbeat` | Scheduler liveness |
| `hourly-tenant-digest` | Crontab-style example |

Customer-1 may enrich tick results via `backend/app/customers/customer_1/jobs.py`.

---

## 10. Repository map

```text
customer-architecture-poc/
├── README.md                              # How to run (ops)
├── ARCHITECTURE_README.md                 # This file — whole architecture
├── FRONTEND_ARCHITECTURE.md               # FE deep dive
├── BACKEND_ARCHITECTURE.md                # BE deep dive
├── DATABASE_ARCHITECTURE.md               # DB + Alembic deep dive
├── CELERY_REDIS_ARCHITECTURE_README.md    # Jobs adaptation deep dive
├── docker-compose.yml
├── db/
│   ├── README.md
│   └── init/01_schemas.sql                # Step 1 bootstrap only
├── backend/
│   ├── JOBS.md
│   ├── migrations/
│   │   ├── platform/                      # generic catalog + job_runs
│   │   ├── base/                          # shared leads DDL
│   │   └── README.md
│   ├── docker-entrypoint.sh               # api | worker | beat
│   └── app/
│       ├── core/                          # base product backend
│       ├── domains/leads/
│       ├── jobs/                          # Celery tasks + tracking + routes
│       └── customers/
│           ├── customer_1/                # API + migrations + jobs enrich
│           ├── customer_2/
│           └── customer_3/                # manifest only (base behaviour)
└── frontend/
    └── app/
        ├── core/                          # base product UI
        └── customers/
            ├── registry.js                # only place to register FE packages
            ├── customer-1/                # overrides
            ├── customer-2/                # config only
            └── customer-3/                # config only
```

---

## 11. Customer matrix (what is implemented)

| Capability | customer-1 | customer-2 | customer-3 |
|---|---|---|---|
| Display | GreenGrid Solar | FinTrust Loans | BaseCo |
| FE extras | Roof size, energy bill + UI overrides | Consent, product type | None |
| API | `/customer-1-endpoint` → integer | `/customer-2-endpoint` → percentage | `/base-endpoint1` → string |
| Schema | `schema_customer_1` | `schema_customer_2` | `schema_customer_3` |
| Extra columns | `roof_size_sqft`, `monthly_energy_bill` | `consent_given`, `product_type`, `disclaimer_id` | — |
| Job enrich | `jobs.py` solar note | base | base |

---

## 12. How to add a new customer (checklist)

Example: **customer-4**

### Bootstrap (ops)

- [ ] `CREATE DATABASE schema_customer_4` + `GRANT` in `db/init/01_schemas.sql` (or ops job)  
- [ ] Apply on environment (fresh volume or root SQL)

### Backend

- [ ] `backend/app/customers/customer_4/manifest.json`  
- [ ] `__init__.py` with optional `router` / `HOOKS`  
- [ ] Optional `migrations/` (after base; set `MIN_BASE_REVISION`)  
- [ ] Optional `jobs.py` enricher  
- [ ] `python -m app.core.migrate_all`

### Frontend

- [ ] `frontend/app/customers/customer-4/config.js` + `index.js`  
- [ ] One line in `frontend/app/customers/registry.js`  
- [ ] Optional slot overrides under `components/` / `hooks/` / `styles/`

### Deploy

- [ ] Backend (API)  
- [ ] Worker / Beat (if new jobs)  
- [ ] Frontend  

**Do not** copy-paste `core/` into the customer folder.

---

## 13. Adaptation guidance (bring this into a real product)

When explaining to developers moving AI SDR / Campaign Management onto this model:

1. **Split base vs customer folders** for FE and BE (no customer `if` forests in core).  
2. **Keep a tenant resolver** on every request / job (`customer_id` explicit).  
3. **Schema-per-tenant** with platform catalog DB (`generic`).  
4. **Alembic in three chains:** platform → base fan-out → customer.  
5. **Move crons out of the API** into Celery Beat + Worker + Redis; track runs.  
6. **Migrate incrementally:** one customer package + one job + one schema delta per PR when possible.  
7. **Customer-3 style onboarding** should remain possible (config/manifest only).

### Suggested rollout order in a real codebase

| Phase | Work |
|---|---|
| P0 | Tenant resolver + schema routing + folder layout |
| P1 | FE `resolveFrontend` / registry pattern |
| P2 | Platform + base + customer Alembic orchestrator |
| P3 | Move first 1–3 APScheduler jobs to Celery |
| P4 | Expand customer packages; retire forks / `UVICORN_WORKERS=1` constraint |

---

## 14. Demo script (10 minutes)

1. `docker compose up --build`  
2. Open http://localhost:3000 — switch customer-1 ↔ customer-2 ↔ customer-3  
   - Show fields, theme, endpoint, result type change  
3. Show API docs http://localhost:8000/docs  
4. Show DB isolation: three schemas, shared `generic.tenants`  
5. Show jobs:  
   - `GET /api/jobs/schedule`  
   - `POST /api/jobs/trigger/lead_status_sync`  
   - `GET /api/jobs/runs` — point out customer-1 `solar_note`  
6. Close with: “Same preference rule on FE, BE, DB, and jobs.”

---

## 15. Success criteria for “we adopted this architecture”

- [ ] Base product code has no hard-coded customer business rules  
- [ ] Each customer delta lives under a customer folder (FE and/or BE)  
- [ ] Tenant identity is resolved per request/job  
- [ ] Schema changes go through Alembic (platform / base / customer order)  
- [ ] Scheduled work does not run inside the API process  
- [ ] Job runs are queryable (history exists)  
- [ ] A base-only customer can go live without custom code  

---

## 16. Related documents

| Document | Use when |
|---|---|
| [README.md](./README.md) | Running the POC |
| [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md) | FE slot/override details |
| [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md) | API, resolver, registry, isolation |
| [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) | `generic`, tenant schemas, Alembic order |
| [backend/migrations/README.md](./backend/migrations/README.md) | Migration commands & onboarding schema |
| [db/README.md](./db/README.md) | Why bootstrap SQL still exists |
| [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md) | Replacing ElevenLabs APScheduler |
| [backend/JOBS.md](./backend/JOBS.md) | Short jobs runbook |
| `plan-poc.md` (repo root) | Original two/three-customer sketch |
| `explore/ARCHITECTURE_FINALIZATION_README.md` | Broader platform target architecture |
