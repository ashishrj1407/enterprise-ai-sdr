"""Platform chain: tenant catalog in the `generic` database.

This is the shared directory of customers — not lead/business data.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "p001_tenants"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("customer_id", sa.String(64), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("schema_name", sa.String(64), nullable=False),
        sa.Column("endpoint", sa.String(128), nullable=False),
        sa.Column("result_type", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tenants")
