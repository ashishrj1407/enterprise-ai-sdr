"""Migration orchestrator — steps 2–5 of the install sequence.

  1. Bootstrap (ops)     → db/init/01_schemas.sql  (empty DBs + GRANTs; not here)
  2. Platform upgrade    → migrations/platform     → `generic`
  3. Base upgrade        → migrations/base         → every schema_customer_*
  4. Customer upgrade    → app/customers/*/migrations
  5. Seed                → catalog + optional demo leads
  6. Deploy              → backend → frontend (Compose / CI)

This module does not create databases. Bootstrap must run first.
"""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import CUSTOMER_SCHEMAS
from migrations.env_common import (
    BACKEND_ROOT,
    MIGRATIONS_ROOT,
    database_url_for_schema,
)

logger = logging.getLogger(__name__)

CUSTOMERS_ROOT = BACKEND_ROOT / "app" / "customers"
REQUIRED_BASE_HEAD = "b001_leads_base"
# Platform head advances with job_runs; migrate_all uses alembic upgrade head.


def _alembic_config(script_location: Path, url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(script_location))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("prepend_sys_path", str(BACKEND_ROOT))
    return cfg


def _upgrade(script_location: Path, url: str, label: str) -> None:
    logger.info("Alembic upgrade head [%s] → %s", label, url.rsplit("/", 1)[-1])
    command.upgrade(_alembic_config(script_location, url), "head")


def _server_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    return urlunparse(parsed._replace(path="/"))


def _require_databases(database_url: str, names: list[str]) -> None:
    """Fail fast if bootstrap (step 1) did not create the required databases."""
    engine = create_engine(_server_url(database_url))
    missing: list[str] = []
    try:
        with engine.connect() as conn:
            for name in names:
                exists = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.SCHEMATA "
                        "WHERE SCHEMA_NAME = :name"
                    ),
                    {"name": name},
                ).scalar()
                if not exists:
                    missing.append(name)
    finally:
        engine.dispose()

    if missing:
        raise RuntimeError(
            "Bootstrap incomplete — missing database(s): "
            + ", ".join(missing)
            + ". Create empty DBs + GRANTs first (db/init/01_schemas.sql or ops job), "
            "then re-run migrate_all. Do not create tables in bootstrap."
        )


def _current_revision(script_location: Path, url: str, version_table: str) -> str | None:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() AND table_name = :t"
                ),
                {"t": version_table},
            ).scalar()
            if not exists:
                return None
            row = conn.execute(text(f"SELECT version_num FROM `{version_table}`")).first()
            return row[0] if row else None
    finally:
        engine.dispose()


def _customer_folder(customer_id: str) -> Path:
    return CUSTOMERS_ROOT / customer_id.replace("-", "_")


def _customer_migrations_dir(customer_id: str) -> Path | None:
    path = _customer_folder(customer_id) / "migrations"
    versions = path / "versions"
    if path.is_dir() and versions.is_dir() and any(versions.glob("*.py")):
        return path
    return None


def _min_base_revision(migrations_dir: Path) -> str | None:
    """Read MIN_BASE_REVISION from the earliest customer revision module if present."""
    versions = sorted((migrations_dir / "versions").glob("*.py"))
    for path in versions:
        if path.name.startswith("_"):
            continue
        text_src = path.read_text(encoding="utf-8")
        for line in text_src.splitlines():
            if line.startswith("MIN_BASE_REVISION"):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


def _tenant_rows_from_manifests() -> list[dict[str, str]]:
    from app.customers import discover_customers, list_customers

    discover_customers()
    rows: list[dict[str, str]] = []
    for manifest in list_customers():
        customer_id = manifest["customer_id"]
        rows.append(
            {
                "customer_id": customer_id,
                "display_name": manifest.get("display_name", customer_id),
                "schema_name": manifest.get(
                    "schema", CUSTOMER_SCHEMAS.get(customer_id, "")
                ),
                "endpoint": manifest.get("endpoint", "/base-endpoint1"),
                "result_type": manifest.get("result_type", "string"),
            }
        )
    return [r for r in rows if r["schema_name"]]


def _read_tenants(platform_url: str) -> list[dict[str, str]]:
    engine = create_engine(platform_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT customer_id, display_name, schema_name, endpoint, result_type "
                    "FROM tenants ORDER BY customer_id"
                )
            )
            return [dict(row._mapping) for row in result]
    except Exception:
        return []
    finally:
        engine.dispose()


def _seed_tenants(platform_url: str, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    engine = create_engine(platform_url)
    try:
        with engine.begin() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM tenants")).scalar() or 0
            if count:
                return
            for row in rows:
                conn.execute(
                    text(
                        "INSERT INTO tenants "
                        "(customer_id, display_name, schema_name, endpoint, result_type) "
                        "VALUES (:customer_id, :display_name, :schema_name, :endpoint, :result_type)"
                    ),
                    row,
                )
            logger.info("Seeded %s tenant row(s) into generic.tenants", len(rows))
    finally:
        engine.dispose()


def _seed_demo_leads(base_url: str, tenants: list[dict[str, str]]) -> None:
    samples = {
        "customer-1": {
            "sql": (
                "INSERT INTO leads "
                "(name, email, company, address, roof_size_sqft, monthly_energy_bill, "
                "result_type, result_value, source) "
                "VALUES ('Seed Green', 'seed@greengrid.example', 'GreenGrid', "
                "'100 Solar Way, Austin TX', 1200, 210.00, 'integer', '84', 'seed')"
            ),
        },
        "customer-2": {
            "sql": (
                "INSERT INTO leads "
                "(name, email, company, address, consent_given, product_type, disclaimer_id, "
                "result_type, result_value, source) "
                "VALUES ('Seed Fin', 'seed@fintrust.example', 'FinTrust', "
                "'12 Lombard St, London', TRUE, 'term_loan', 'DISCLAIMER-FT-UK-v6', "
                "'percentage', '72.5', 'seed')"
            ),
        },
        "customer-3": {
            "sql": (
                "INSERT INTO leads "
                "(name, email, company, address, result_type, result_value, source) "
                "VALUES ('Seed Base', 'seed@baseco.example', 'BaseCo', "
                "'1 Main Street', 'string', 'qualified:Seed Base', 'seed')"
            ),
        },
    }

    for tenant in tenants:
        sample = samples.get(tenant["customer_id"])
        if not sample:
            continue
        url = database_url_for_schema(base_url, tenant["schema_name"])
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM leads")).scalar() or 0
                if count:
                    continue
                conn.execute(text(sample["sql"]))
                logger.info("Seeded demo lead in %s", tenant["schema_name"])
        finally:
            engine.dispose()


def migrate_all() -> None:
    """Steps 2–5: platform → base → customer → seed. Requires step 1 bootstrap."""
    settings = get_settings()
    base_url = settings.database_url
    platform_db = settings.platform_database
    platform_url = database_url_for_schema(base_url, platform_db)

    manifest_rows = _tenant_rows_from_manifests()
    required_dbs = [platform_db] + [r["schema_name"] for r in manifest_rows]
    logger.info("Step 1 check — require bootstrap databases: %s", ", ".join(required_dbs))
    _require_databases(base_url, required_dbs)

    # 2) Platform catalog tables
    logger.info("Step 2 — platform upgrade → %s", platform_db)
    _upgrade(MIGRATIONS_ROOT / "platform", platform_url, "platform")

    # Seed catalog early so later runs can prefer DB list
    _seed_tenants(platform_url, manifest_rows)
    tenants = _read_tenants(platform_url) or manifest_rows
    if not tenants:
        raise RuntimeError("No tenants found in generic.tenants or customer manifests")

    base_scripts = MIGRATIONS_ROOT / "base"
    # 3) Base fan-out
    logger.info("Step 3 — base upgrade fan-out (%s schemas)", len(tenants))
    for tenant in tenants:
        schema = tenant["schema_name"]
        url = database_url_for_schema(base_url, schema)
        _upgrade(base_scripts, url, f"base:{schema}")

        current = _current_revision(base_scripts, url, "alembic_version_base")
        if current != REQUIRED_BASE_HEAD:
            script = ScriptDirectory(str(base_scripts))
            heads = set(script.get_heads())
            if current not in heads:
                raise RuntimeError(
                    f"{schema} base revision {current!r} is not at head {heads}"
                )

    # 4) Customer overrides (after base)
    logger.info("Step 4 — customer upgrades")
    for tenant in tenants:
        customer_id = tenant["customer_id"]
        migrations_dir = _customer_migrations_dir(customer_id)
        if not migrations_dir:
            logger.info("No customer migrations for %s — base schema only", customer_id)
            continue

        schema = tenant["schema_name"]
        url = database_url_for_schema(base_url, schema)
        min_base = _min_base_revision(migrations_dir) or REQUIRED_BASE_HEAD
        current_base = _current_revision(
            base_scripts, url, "alembic_version_base"
        )
        if current_base is None:
            raise RuntimeError(
                f"Cannot apply {customer_id} migrations: base not applied on {schema}"
            )
        script = ScriptDirectory(str(base_scripts))
        applied = {current_base}
        for rev in script.walk_revisions(base="base", head=current_base):
            applied.add(rev.revision)
            down = rev.down_revision
            if isinstance(down, str):
                applied.add(down)
            elif down:
                applied.update(down)
        if min_base not in applied:
            raise RuntimeError(
                f"{customer_id} requires base revision {min_base!r} before overrides; "
                f"{schema} is at {current_base!r}"
            )

        _upgrade(migrations_dir, url, f"customer:{customer_id}")

    # 5) Demo seed
    logger.info("Step 5 — seed catalog/demo data (if empty)")
    _seed_demo_leads(base_url, tenants)
    logger.info(
        "Steps 2–5 complete (platform=%s, tenants=%s). Step 6: deploy backend → frontend.",
        platform_db,
        ", ".join(t["customer_id"] for t in tenants),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_all()
