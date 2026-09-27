# Install & migration sequence

> Full database architecture: [DATABASE_ARCHITECTURE.md](../../DATABASE_ARCHITECTURE.md)  
> Backend architecture: [BACKEND_ARCHITECTURE.md](../../BACKEND_ARCHITECTURE.md)

Aligned order for a new environment:

```text
1. Bootstrap          db/init/01_schemas.sql     empty DBs + GRANTs (no tables)
2. Platform upgrade   migrations/platform        tables in `generic`
3. Base upgrade       migrations/base            shared tables → every schema_customer_*
4. Customer upgrade   app/customers/*/migrations extras → that schema only
5. Seed               migrate_all                catalog + optional demo leads
6. Deploy             backend → frontend         API then UI
```

Docker Compose: step 1 on first DB volume; steps 2–5 via backend entrypoint
(`python -m app.core.migrate_all`); step 6 is container start order
(backend healthy → frontend).

## Step details

| Step | Owner | Creates tables? | Target |
|---|---|---|---|
| 1 Bootstrap | Ops / MySQL init | No | `generic`, `schema_customer_*` |
| 2 Platform | Alembic | Yes | `generic` (`tenants`, …) |
| 3 Base | Alembic fan-out | Yes | every tenant schema (shared `leads`, …) |
| 4 Customer | Alembic per tenant | Yes (extras) | matching schema only |
| 5 Seed | `migrate_all` | No (rows only) | catalog + demo leads if empty |
| 6 Deploy | Compose / CI | — | backend then frontend |

## Chains (Alembic)

| Order | Chain | Location | Version table |
|---|---|---|---|
| 2 | Platform | `migrations/platform` | `alembic_version` in `generic` |
| 3 | Base | `migrations/base` | `alembic_version_base` per tenant schema |
| 4 | Customer | `app/customers/<id>/migrations` | `alembic_version_customer` per tenant schema |

`generic` is the shared tenant **catalog**. Lead data lives only in `schema_customer_*`.

## Run steps 2–5

```bash
# From backend/ (also run automatically by Docker entrypoint)
python -m app.core.migrate_all
```

Bootstrap (step 1) must already have created the databases. `migrate_all` verifies
they exist and fails with a clear error if bootstrap was skipped.

## Adding a base column (all customers)

1. Add a revision under `migrations/base/versions/`
2. Run `migrate_all` — fan-out applies to every tenant schema
3. Update backend `core/` + frontend `core/`
4. Deploy backend → frontend

## Adding a customer column

1. Add a revision under `app/customers/customer_N/migrations/versions/`
2. Set `MIN_BASE_REVISION = "…"` in that file
3. Update that customer’s backend + frontend packages only
4. Run `migrate_all`, then deploy backend → frontend

Customer-3 has no `migrations/` folder — base schema only (steps 1–3 + 5).

## Onboarding customer-4

1. Bootstrap: `CREATE DATABASE schema_customer_4` + `GRANT` (extend `db/init/01_schemas.sql` or ops job)
2. Add manifest / optional `migrations/` under `app/customers/customer_4/`
3. `python -m app.core.migrate_all`
4. Deploy backend → frontend
