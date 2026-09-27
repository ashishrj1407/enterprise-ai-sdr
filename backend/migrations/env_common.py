"""Shared Alembic helpers for platform / base / customer chains."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, urlunparse

from alembic import context
from sqlalchemy import create_engine, pool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_ROOT = BACKEND_ROOT / "migrations"


def database_url_for_schema(base_url: str, schema: str) -> str:
    """Rewrite SQLAlchemy URL path to target a specific MySQL database/schema."""
    parsed = urlparse(base_url)
    return urlunparse(parsed._replace(path=f"/{schema}"))


def run_migrations_online(*, version_table: str) -> None:
    """Standard online migration runner used by every chain's env.py."""
    config = context.config
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url is required for migrations")

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table=version_table,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
