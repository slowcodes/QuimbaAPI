"""change experiment result reading parameter value to text

Revision ID: 7d3a9c5e8f1b
Revises: 5a6b7c8d9e0f
Create Date: 2026-05-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7d3a9c5e8f1b"
down_revision: Union[str, None] = "5a6b7c8d9e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "lab_experiment_result_reading",
        "parameter_value",
        existing_type=sa.String(length=100),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "lab_experiment_result_reading",
        "parameter_value",
        existing_type=sa.Text(),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
