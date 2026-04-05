"""add stacking_order to lab_experiment_parameter

Revision ID: 8c4f8b31a6d2
Revises: 6a9b3f2c1d0e
Create Date: 2026-04-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c4f8b31a6d2"
down_revision: Union[str, None] = "6a9b3f2c1d0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lab_experiment_parameter",
        sa.Column("stacking_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.alter_column("lab_experiment_parameter", "stacking_order", server_default=None)


def downgrade() -> None:
    op.drop_column("lab_experiment_parameter", "stacking_order")
