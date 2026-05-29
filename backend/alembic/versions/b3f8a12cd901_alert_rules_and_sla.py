"""alert rules and sla

Revision ID: b3f8a12cd901
Revises: 9124d24961dd
Create Date: 2026-05-29 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3f8a12cd901"
down_revision: Union[str, None] = "9124d24961dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("monitored_services", sa.Column("failure_threshold", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("monitored_services", sa.Column("latency_threshold_ms", sa.Integer(), nullable=False, server_default="2000"))
    op.add_column("monitored_services", sa.Column("incident_severity", sa.String(length=20), nullable=False, server_default="CRITICAL"))


def downgrade() -> None:
    op.drop_column("monitored_services", "incident_severity")
    op.drop_column("monitored_services", "latency_threshold_ms")
    op.drop_column("monitored_services", "failure_threshold")
