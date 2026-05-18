"""update user notification message payload

Revision ID: f2a7c8d9e1b0
Revises: 16574d5c59d6
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2a7c8d9e1b0"
down_revision: Union[str, None] = "16574d5c59d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user_notification",
        sa.Column("description", sa.String(length=255), nullable=True),
    )
    op.execute("UPDATE user_notification SET description = message WHERE description IS NULL")
    op.alter_column(
        "user_notification",
        "message",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=False,
        nullable=True,
    )
    op.execute("UPDATE user_notification SET message = '[]' WHERE message IS NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE user_notification SET message = LEFT(COALESCE(description, message, ''), 255)")
    op.alter_column(
        "user_notification",
        "message",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True,
        nullable=False,
    )
    op.drop_column("user_notification", "description")
