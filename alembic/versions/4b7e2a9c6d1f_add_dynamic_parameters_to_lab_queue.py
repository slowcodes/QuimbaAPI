"""add dynamic parameters to lab queue

Revision ID: 4b7e2a9c6d1f
Revises: 9a2e6c4f1b7d
Create Date: 2026-05-09 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b7e2a9c6d1f"
down_revision: Union[str, None] = "9a2e6c4f1b7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lab_dynamic_experiment_parameter",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parameter", sa.String(length=50), nullable=True),
        sa.Column("parameter_value", sa.String(length=50), nullable=True),
        sa.Column("lab_service_queue_id", sa.Integer(), nullable=True),
        sa.Column("exp_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["exp_id"], ["lab_experiment.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["lab_service_queue_id"], ["lab_service_queue.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lab_dynamic_experiment_parameter_id"),
        "lab_dynamic_experiment_parameter",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_lab_dynamic_experiment_parameter_id"),
        table_name="lab_dynamic_experiment_parameter",
    )
    op.drop_table("lab_dynamic_experiment_parameter")
