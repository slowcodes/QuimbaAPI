"""add audit fields to lab observation result template

Revision ID: 4c9d2e7a1b5f
Revises: 3b8f1a2c9d4e
Create Date: 2026-05-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c9d2e7a1b5f"
down_revision: Union[str, None] = "3b8f1a2c9d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lab_observation_result_template",
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "lab_observation_result_template",
        sa.Column("created_by", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lab_observation_result_template_created_by_users",
        "lab_observation_result_template",
        "users",
        ["created_by"],
        ["id"],
        ondelete="cascade",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_lab_observation_result_template_created_by_users",
        "lab_observation_result_template",
        type_="foreignkey",
    )
    op.drop_column("lab_observation_result_template", "created_by")
    op.drop_column("lab_observation_result_template", "created_at")
