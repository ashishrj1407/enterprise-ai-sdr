# Database bootstrap

## Step 1 only — empty databases + grants

`init/01_schemas.sql` runs on **first MySQL install** (empty Docker volume).

It creates:

- `generic` — platform catalog DB
- `schema_customer_N` — one empty DB per tenant
- `GRANT` for the app user (`poc`)

It does **not** create tables. Table DDL and seed are steps 2–5 via:

```bash
python -m app.core.migrate_all
```

See [DATABASE_ARCHITECTURE.md](../DATABASE_ARCHITECTURE.md) for the full database design, and [backend/migrations/README.md](../backend/migrations/README.md) for migration commands.
