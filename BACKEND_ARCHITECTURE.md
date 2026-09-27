# Backend Architecture — Base-First with Customer Override

> Companion guide for the Customer Architecture POC **backend**.  
> Whole-system overview: [ARCHITECTURE_README.md](./ARCHITECTURE_README.md)  
> Database deep dive: [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md)  
> Jobs deep dive: [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md)  
> Runbook: [README.md](./README.md)

This document explains how the **base FastAPI product** is shared by all customers, and how **customer-specific API / hooks / jobs** take precedence without forking core.

---

## 1. Goals

| Principle | Meaning in this POC |
|---|---|
| **Base-first** | Complete default API + domain logic live under `backend/app/core/` and `domains/` |
| **Customer override** | Routers, hooks, migrations, and job enrichers under `app/customers/<id>/` win when present |
| **Fallback** | No customer router → use base routes (`/base-endpoint1`) |
| **Extensible** | New customer = folder + `manifest.json` (+ optional router/migrations/jobs) |
| **Portable** | Core does not hard-code customer scoring or fields |
| **Isolated** | Wrong `X-Customer-Id` on a foreign customer endpoint → HTTP 403 |
| **Tenant-safe** | Every request gets an immutable `TenantContext`; DB uses that schema only |

---

## 2. High-level layout

```text
backend/app/
├── main.py                      # FastAPI app: mount base + jobs + discovered customer routers
├── core/                        # BASE PRODUCT
│   ├── config.py                # settings (DB, Redis, host map, platform DB name)
│   ├── resolver.py              # host / header → customer_id
│   ├── tenant.py                # TenantContext dependency
│   ├── extension_registry.py    # discover manifests, routers, HOOKS
│   ├── database.py              # engine + tenant_session (USE schema)
│   ├── migrate_all.py           # Alembic orchestrator (steps 2–5)
│   ├── celery_app.py            # Celery + Beat schedule
│   └── routes/base.py           # /health /customers /me /base-endpoint1 /leads
├── domains/
│   └── leads/                   # base qualify + list_leads
├── jobs/                        # BASE jobs API + tasks + tracking
│   ├── routes.py                # /api/jobs/*
│   ├── tasks.py                 # Celery tasks (fan-out)
│   └── tracking.py              # generic.job_runs writers
└── customers/                   # CUSTOMER DELTAS ONLY
    ├── customer_1/              # router + migrations + jobs.py
    ├── customer_2/              # router + migrations
    └── customer_3/              # manifest only → base API behaviour
```

---

## 3. Request pipeline

```text
HTTP request
    │
    ├─ Optional: X-Customer-Id
    ├─ Optional: Host / X-Forwarded-Host
    ▼
resolve_customer()          # core/resolver.py
    │
    ▼
get_tenant_context()        # core/tenant.py
    │  loads manifest → display_name, schema_name
    ▼
TenantContext (frozen)
    │
    ├─ base route        → domains/leads (string result)
    ├─ customer route    → customers/customer_N (gated to that id)
    └─ tenant_session()  → USE `schema_customer_N`
```

### Identity resolution order

1. `X-Customer-Id` (demo UI / curl / FE proxy)  
2. Host map (`customer-1.localhost` → `customer-1`)  
3. Default (`customer-3`)

**Do not confuse** this with the frontend `resolveFrontend` merge engine. Backend resolver answers *who*; frontend resolver answers *which UI*.

---

## 4. Extension registry

`core/extension_registry.py` scans `app/customers/*`:

| Artifact | Effect |
|---|---|
| `manifest.json` | Catalog metadata (schema, endpoint, result_type, extras) |
| `router` on package | Mounted under `/api` |
| `HOOKS` dict | Optional soft extension points (e.g. `before_qualify`) |

Core never lists customer IDs for business logic. Discovery is folder-based.

Example manifest fields:

```json
{
  "customer_id": "customer-1",
  "display_name": "GreenGrid Solar (Customer A)",
  "schema": "schema_customer_1",
  "endpoint": "/customer-1-endpoint",
  "result_type": "integer",
  "extra_fields": ["roof_size_sqft", "monthly_energy_bill"],
  "min_base_revision": "b001_leads_base"
}
```

---

## 5. Base vs customer API behaviour

| Customer | Endpoint | Result type | Implementation |
|---|---|---|---|
| customer-3 (base) | `POST /api/base-endpoint1` | string | `domains/leads.qualify_lead_base` |
| customer-1 | `POST /api/customer-1-endpoint` | integer | `customers/customer_1` router |
| customer-2 | `POST /api/customer-2-endpoint` | percentage | `customers/customer_2` router |

Shared reads:

- `GET /api/leads` — lists from **active tenant schema only**  
- `GET /api/me` — returns resolved tenant + manifest summary  

Isolation:

- Calling `/customer-1-endpoint` with `X-Customer-Id: customer-2` → **403**  
- Data from schema_customer_1 never returned for customer-2 context  

---

## 6. Database access pattern

```python
with tenant_session(customer_id) as db:
    db.execute(text("INSERT INTO leads ..."))
```

`tenant_session`:

1. Maps `customer_id` → schema name  
2. `USE \`schema_customer_N\``  
3. Commits / rolls back on that connection  

Platform catalog access (tenants, job_runs) uses the `generic` database URL — not a tenant schema.

See [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) for schemas, Alembic chains, and bootstrap.

---

## 7. Jobs on the backend (summary)

| Piece | Location | Role |
|---|---|---|
| Celery app + Beat schedule | `core/celery_app.py` | Outside the API process |
| Tasks | `jobs/tasks.py` | Fan-out + per-tenant work |
| Tracking | `jobs/tracking.py` | Write `generic.job_runs` |
| HTTP observe/trigger | `jobs/routes.py` | `/api/jobs/*` |
| Customer enrich | `customers/customer_1/jobs.py` | Optional override |

Rule: **API may enqueue; Beat schedules; Worker executes.** FastAPI does not embed APScheduler.

Details: [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md)

---

## 8. Process entrypoints (same image)

`docker-entrypoint.sh` roles:

| Command | Process |
|---|---|
| `api` | `migrate_all` then `uvicorn` |
| `worker` | `celery worker` |
| `beat` | `celery beat` |

Compose wires the same backend image three ways (`backend`, `worker`, `beat`).

---

## 9. Preference / override rules (backend)

| Concern | Preference |
|---|---|
| HTTP route for a feature | customer router if mounted → else base route |
| Hook | customer `HOOKS[name]` if registered → else core default |
| Job enrichment | `customers/<id>/jobs.py` if importable → else base payload |
| Schema extras | customer Alembic after base → else base columns only |

**Never** add `if customer_id == "customer-1"` forests inside `core/`.

---

## 10. How to add backend support for customer-4

1. Create `app/customers/customer_4/manifest.json`  
2. Create `__init__.py` — optional `router`, `HOOKS`  
3. Optional dedicated endpoint module (integer/percentage/custom)  
4. Optional `migrations/` (see database guide)  
5. Optional `jobs.py` with `enrich_status_sync` (or similar)  
6. Ensure bootstrap created `schema_customer_4`  
7. Run `python -m app.core.migrate_all`  
8. Deploy API (+ worker/beat if new tasks)

No edits required in `core/routes/base.py` for a dedicated customer endpoint.

---

## 11. Testing focus

| Area | What to prove |
|---|---|
| Resolver | header / host / default |
| Isolation | cross-tenant endpoint → 403 |
| Base path | customer-3 uses `/base-endpoint1` |
| Customer path | correct result_type + persistence in own schema |
| Registry | manifests discovered without hard-coded core lists |

```bash
cd backend
pytest -q
```

---

## 12. Related documents

| Doc | Contents |
|---|---|
| [ARCHITECTURE_README.md](./ARCHITECTURE_README.md) | Whole POC |
| [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) | Schemas + Alembic |
| [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md) | FE override model |
| [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md) | Jobs adaptation |
| [backend/migrations/README.md](./backend/migrations/README.md) | Migration runbook |
| [backend/JOBS.md](./backend/JOBS.md) | Jobs ops curls |
