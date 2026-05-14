"""remove parameter id from dynamic parameters

Revision ID: 8f2c1d7e4a6b
Revises: 4b7e2a9c6d1f
Create Date: 2026-05-09 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f2c1d7e4a6b"
down_revision: Union[str, None] = "4b7e2a9c6d1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE lab_dynamic_experiment_parameter "
        "DROP COLUMN IF EXISTS parameter_id"
    )


def downgrade() -> None:
    op.add_column(
        "lab_dynamic_experiment_parameter",
        sa.Column("parameter_id", sa.Integer(), nullable=True),
    )
