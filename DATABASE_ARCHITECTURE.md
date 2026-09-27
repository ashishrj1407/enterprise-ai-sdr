# Database Architecture — Platform, Base, Customer

> Companion guide for the Customer Architecture POC **database & migrations**.  
> Whole-system overview: [ARCHITECTURE_README.md](./ARCHITECTURE_README.md)  
> Backend deep dive: [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)  
> Migration commands: [backend/migrations/README.md](./backend/migrations/README.md)  
> Bootstrap only: [db/README.md](./db/README.md)

This document explains **schema-per-tenant** design, the **`generic` platform catalog**, and the **Alembic order**: bootstrap → platform → base → customer → seed.

---

## 1. Goals

| Principle | Meaning in this POC |
|---|---|
| **Schema-per-tenant** | Each customer has an isolated MySQL database/schema |
| **Shared catalog** | `generic` holds tenant directory + job run history — not lead rows |
| **Base-first DDL** | Shared `leads` shape applied to every tenant schema first |
| **Customer override after base** | Extra columns/tables only in that customer’s schema, only after base head |
| **Bootstrap ≠ migrations** | Ops creates empty DBs + grants; Alembic creates tables |
| **No cross-tenant reads** | App always `USE`s one customer schema per request/job |

---

## 2. Logical model

```text
MySQL instance
├── generic                          # PLATFORM catalog (not business leads)
│   ├── tenants                      # who exists → which schema / endpoint
│   ├── job_runs                     # Celery run history
│   └── alembic_version              # platform chain
│
├── schema_customer_1                # TENANT A data
│   ├── leads                        # base columns + solar extras
│   ├── alembic_version_base
│   └── alembic_version_customer
│
├── schema_customer_2                # TENANT B data
│   ├── leads                        # base columns + consent extras
│   ├── alembic_version_base
│   └── alembic_version_customer
│
└── schema_customer_3                # TENANT C data (base only)
    ├── leads                        # base columns only
    └── alembic_version_base
```

### What `generic` is for

| Provides | Does **not** provide |
|---|---|
| List of customers | Lead / campaign business rows |
| `schema_name` mapping | Fan-out of DDL by itself |
| Job observability (`job_runs`) | Customer-specific columns |

Updating `generic` (platform upgrade) **never** automatically alters `schema_customer_*`.  
An orchestrator **reads** `tenants` (or manifests) and then runs base/customer chains per schema.

---

## 3. Install sequence (mandatory)

```text
1. Bootstrap     db/init/01_schemas.sql      empty DBs + GRANTs (NO tables)
2. Platform      migrations/platform         tables in `generic`
3. Base          migrations/base             fan-out → every schema_customer_*
4. Customer      app/customers/*/migrations  extras → one schema only
5. Seed          migrate_all                 tenants + demo leads if empty
6. Deploy        API → Worker/Beat → FE
```

| Step | Creates tables? | Runner |
|---|---|---|
| 1 Bootstrap | No | MySQL Docker init (root) / ops |
| 2 Platform | Yes | `python -m app.core.migrate_all` |
| 3 Base | Yes | same (loops tenants) |
| 4 Customer | Yes (deltas) | same (only if migrations/ exists) |
| 5 Seed | Rows only | same |
| 6 Deploy | — | Compose |

`migrate_all` **requires** step 1. It verifies databases exist and fails clearly if bootstrap was skipped. It does **not** `CREATE DATABASE` as the app user.

---

## 4. Bootstrap (step 1)

File: `db/init/01_schemas.sql` (mounted into MySQL `docker-entrypoint-initdb.d`).

Creates:

- `generic`
- `schema_customer_1` / `_2` / `_3`
- `GRANT` for app user `poc`

Does **not** create `tenants`, `leads`, or any columns.

Why Alembic cannot replace this in the default Compose setup:

- App user typically cannot create databases or grant itself access  
- Init runs as privileged MySQL bootstrap before the API starts  

Details: [db/README.md](./db/README.md)

---

## 5. Alembic chains

| Order | Chain | Location | Target | Version table |
|---|---|---|---|---|
| 2 | Platform | `backend/migrations/platform` | `generic` | `alembic_version` |
| 3 | Base | `backend/migrations/base` | every `schema_customer_*` | `alembic_version_base` |
| 4 | Customer | `backend/app/customers/<id>/migrations` | that schema only | `alembic_version_customer` |

### Current revisions (POC)

| Revision | Chain | Effect |
|---|---|---|
| `p001_tenants` | platform | Create `tenants` |
| `p002_job_runs` | platform | Create `job_runs` |
| `b001_leads_base` | base | Shared `leads` table (incl. `address`) |
| `c1_001_solar_cols` | customer-1 | `roof_size_sqft`, `monthly_energy_bill` |
| `c2_001_consent_cols` | customer-2 | `consent_given`, `product_type`, `disclaimer_id` |

Customer-3 has **no** customer chain — base schema only.

### Customer gate

Customer revisions declare:

```python
MIN_BASE_REVISION = "b001_leads_base"
```

Orchestrator refuses customer upgrades until that base revision is present on the schema.

---

## 6. Table ownership rules (avoid conflicts)

| Owner | May do | Must not do |
|---|---|---|
| **Base chain** | Create/alter shared columns on all tenants | Encode customer-1-only columns |
| **Customer chain** | `ADD COLUMN` / `CREATE TABLE` for that tenant | Rewrite base history; change base column types incompatibly |
| **Platform chain** | Catalog / ops tables in `generic` | Store per-tenant lead rows |

“Customer overrides take precedence” means:

> Customer DDL runs **later** and **extends** the schema — it does not rewrite base migration history.

Prefer expand → deploy code → optional contract for breaking changes.

---

## 7. Per-customer schema shape (implemented)

### Base columns (`leads`) — all tenants

`id`, `name`, `email`, `company`, `address`, `result_type`, `result_value`, `source`, `created_at`

### customer-1 extras

`roof_size_sqft`, `monthly_energy_bill`

### customer-2 extras

`consent_given`, `product_type`, `disclaimer_id`

### customer-3

Base columns only.

---

## 8. How runtime uses schemas

```text
Request/Job with customer_id
        │
        ▼
CUSTOMER_SCHEMAS / tenants.schema_name
        │
        ▼
tenant_session → USE `schema_customer_N`
        │
        ▼
SQL against leads (and only that schema’s objects)
```

Platform queries (list tenants, insert job_runs) use database `generic`.

---

## 9. Seed behaviour

After migrations, `migrate_all`:

1. Inserts into `generic.tenants` from manifests if empty  
2. Inserts one demo lead per tenant schema if `leads` is empty  

Seed is **idempotent** (skips when rows exist). It is not a substitute for migrations.

---

## 10. Adding schema support for customer-4

1. **Bootstrap:**  
   `CREATE DATABASE schema_customer_4` + `GRANT` (extend `db/init/01_schemas.sql` or ops)  
2. **Manifest:** point `schema` to `schema_customer_4`  
3. **Base:** `migrate_all` applies `b001_leads_base` (and later base heads) automatically  
4. **Optional customer chain:**  
   `app/customers/customer_4/migrations/versions/...` with `MIN_BASE_REVISION`  
5. Re-run `python -m app.core.migrate_all`  
6. Deploy backend that writes the new columns, then frontend fields  

### Adding a **shared** column for everyone

1. New revision under `migrations/base/versions/`  
2. `migrate_all` fans out to all tenant schemas  
3. Update base backend domain + base frontend fields  
4. Deploy backend → frontend  

### Adding a **customer-only** column

1. New revision under that customer’s `migrations/versions/`  
2. Ensure `MIN_BASE_REVISION` is satisfied  
3. Update only that customer’s API + FE package  
4. `migrate_all` + deploy  

---

## 11. Operational commands

```bash
# Full steps 2–5 (Docker API entrypoint also runs this)
cd backend
python -m app.core.migrate_all

# Recreate empty DBs (re-run bootstrap)
docker compose down -v
docker compose up --build
```

Inspect:

```bash
docker exec -it poc_db mysql -upoc -ppocpass -e "SHOW DATABASES; SELECT * FROM generic.tenants;"
docker exec -it poc_db mysql -upoc -ppocpass -e "SHOW COLUMNS FROM schema_customer_1.leads;"
```

---

## 12. Talking points for developers

1. **`generic` is a phone book; tenant schemas are the apartments.**  
2. **Bootstrap builds empty rooms; Alembic installs furniture.**  
3. **Base first, customer second — always.**  
4. **Platform upgrade does not touch lead tables.**  
5. **Customer-3 proves base-only schema onboarding.**  

---

## 13. Related documents

| Doc | Contents |
|---|---|
| [ARCHITECTURE_README.md](./ARCHITECTURE_README.md) | Whole POC |
| [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md) | API / tenancy / registry |
| [backend/migrations/README.md](./backend/migrations/README.md) | Short migration runbook |
| [db/README.md](./db/README.md) | Bootstrap-only note |
| [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md) | FE overrides |
| [CELERY_REDIS_ARCHITECTURE_README.md](./CELERY_REDIS_ARCHITECTURE_README.md) | `job_runs` consumers |
