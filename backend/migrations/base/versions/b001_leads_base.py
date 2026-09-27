"""Base chain: shared leads table shape for every tenant schema.

Customer-specific columns are NOT created here — they live in
app/customers/<id>/migrations and run after this chain.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b001_leads_base"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("company", sa.String(120), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("result_type", sa.String(32), nullable=False),
        sa.Column("result_value", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("leads")
