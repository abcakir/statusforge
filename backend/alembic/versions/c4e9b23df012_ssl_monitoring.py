"""ssl monitoring

Revision ID: c4e9b23df012
Revises: b3f8a12cd901
Create Date: 2026-05-29 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e9b23df012"
down_revision: Union[str, None] = "b3f8a12cd901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("monitored_services", sa.Column("ssl_expires_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("monitored_services", sa.Column("ssl_checked_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("monitored_services", "ssl_checked_at")
    op.drop_column("monitored_services", "ssl_expires_at")
