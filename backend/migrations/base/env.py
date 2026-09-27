"""Alembic env for the shared base product chain (fan-out to each tenant schema)."""

from alembic import context

from migrations.env_common import run_migrations_online

VERSION_TABLE = "alembic_version_base"


def run_migrations_offline() -> None:
    raise RuntimeError("Offline migrations are not used in this POC")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online(version_table=VERSION_TABLE)
