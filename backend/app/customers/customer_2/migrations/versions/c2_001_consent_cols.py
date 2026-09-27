"""Customer-2 overrides: consent / product columns on leads.

Requires base revision b001_leads_base on schema_customer_2 first.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

MIN_BASE_REVISION = "b001_leads_base"

revision: str = "c2_001_consent_cols"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("consent_given", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "leads",
        sa.Column("product_type", sa.String(64), nullable=True),
    )
    op.add_column(
        "leads",
        sa.Column("disclaimer_id", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("leads", "disclaimer_id")
    op.drop_column("leads", "product_type")
    op.drop_column("leads", "consent_given")
