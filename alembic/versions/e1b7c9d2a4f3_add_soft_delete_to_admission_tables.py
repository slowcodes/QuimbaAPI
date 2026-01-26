"""add soft delete to admission tables

Revision ID: e1b7c9d2a4f3
Revises: d9421a01634d
Create Date: 2026-01-24 02:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1b7c9d2a4f3"
down_revision: Union[str, None] = "d9421a01634d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "admission",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "admission_ward",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "admission_bed",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "admission_ward_room",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.alter_column("admission", "is_deleted", server_default=None)
    op.alter_column("admission_ward", "is_deleted", server_default=None)
    op.alter_column("admission_bed", "is_deleted", server_default=None)
    op.alter_column("admission_ward_room", "is_deleted", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("admission_ward_room", "is_deleted")
    op.drop_column("admission_bed", "is_deleted")
    op.drop_column("admission_ward", "is_deleted")
    op.drop_column("admission", "is_deleted")
