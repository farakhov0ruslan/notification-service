"""drop_delivered_at

Revision ID: c1d3e2f4a5b6
Revises: b376595de8da
Create Date: 2026-04-26 18:00:00.000000

"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1d3e2f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b376595de8da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("NotificationTable", "delivered_at", schema="notification")


def downgrade() -> None:
    op.add_column(
        "NotificationTable",
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        schema="notification",
    )
