"""Generic Alembic env for a single customer's override chain."""

from migrations.env_common import run_migrations_online

VERSION_TABLE = "alembic_version_customer"


def run_migrations_offline() -> None:
    raise RuntimeError("Offline migrations are not used in this POC")


if True:
    run_migrations_online(version_table=VERSION_TABLE)
