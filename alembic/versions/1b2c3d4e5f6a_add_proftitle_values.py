"""add prof title values

Revision ID: 1b2c3d4e5f6a
Revises: e1b7c9d2a4f3
Create Date: 2026-01-24 02:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b2c3d4e5f6a"
down_revision: Union[str, None] = "e1b7c9d2a4f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    enum_name = "proftitle"
    values = ["Miss", "HRH", "Barr", "Rev", "Sis", "Bishop", "Arc", "V.Rev", "Rev Fr"]
    for value in values:
        op.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_type t
                        JOIN pg_enum e ON t.oid = e.enumtypid
                        WHERE t.typname = '{enum_name}' AND e.enumlabel = '{value}'
                    ) THEN
                        ALTER TYPE {enum_name} ADD VALUE '{value}';
                    END IF;
                END $$;
                """
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
