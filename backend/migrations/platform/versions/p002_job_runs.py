"""Platform chain: job run history for Celery Beat / worker observability.

Replaces untracked in-process APScheduler ticks from AI_SDR CampaignManagement.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "p002_job_runs"
down_revision: Union[str, None] = "p001_tenants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.String(120), nullable=False),
        sa.Column("customer_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("celery_task_id", sa.String(64), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.TIMESTAMP,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.TIMESTAMP, nullable=True),
    )
    op.create_index("ix_job_runs_job_name", "job_runs", ["job_name"])
    op.create_index("ix_job_runs_started_at", "job_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_job_runs_started_at", table_name="job_runs")
    op.drop_index("ix_job_runs_job_name", table_name="job_runs")
    op.drop_table("job_runs")
