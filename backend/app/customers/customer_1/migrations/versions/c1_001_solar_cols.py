"""Customer-1 overrides: solar-specific columns on leads.

Requires base revision b001_leads_base on schema_customer_1 first.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Declared so the orchestrator can gate this chain.
MIN_BASE_REVISION = "b001_leads_base"

revision: str = "c1_001_solar_cols"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("roof_size_sqft", sa.Integer(), nullable=True),
    )
    op.add_column(
        "leads",
        sa.Column("monthly_energy_bill", sa.Numeric(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("leads", "monthly_energy_bill")
    op.drop_column("leads", "roof_size_sqft")
