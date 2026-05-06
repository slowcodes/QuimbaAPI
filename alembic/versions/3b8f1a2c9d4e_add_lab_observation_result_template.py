"""add lab observation result template

Revision ID: 3b8f1a2c9d4e
Revises: 8c4f8b31a6d2
Create Date: 2026-05-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3b8f1a2c9d4e"
down_revision: Union[str, None] = "8c4f8b31a6d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lab_observation_result_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template", sa.Text(), nullable=True),
        sa.Column("template_desc", sa.String(length=150), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lab_observation_result_template_id"),
        "lab_observation_result_template",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_lab_observation_result_template_id"),
        table_name="lab_observation_result_template",
    )
    op.drop_table("lab_observation_result_template")
