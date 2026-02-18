"""add file to ui control type

Revision ID: 6a9b3f2c1d0e
Revises: 1b2c3d4e5f6a
Create Date: 2026-02-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a9b3f2c1d0e"
down_revision: Union[str, None] = "1b2c3d4e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("conf_setting", sa.Column("param_desc", sa.String(length=200), nullable=True))

    op.execute(
        sa.text(
            """
            DO $$
            DECLARE enum_type_name text;
            BEGIN
                SELECT t.typname
                INTO enum_type_name
                FROM pg_type t
                JOIN pg_attribute a ON a.atttypid = t.oid
                JOIN pg_class c ON c.oid = a.attrelid
                WHERE c.relname = 'conf_setting'
                  AND a.attname = 'ui_control_type'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                LIMIT 1;

                IF enum_type_name IS NOT NULL
                   AND NOT EXISTS (
                       SELECT 1
                       FROM pg_type t
                       JOIN pg_enum e ON t.oid = e.enumtypid
                       WHERE t.typname = enum_type_name
                         AND e.enumlabel = 'File'
                   )
                THEN
                    EXECUTE format('ALTER TYPE %I ADD VALUE %L', enum_type_name, 'File');
                END IF;
            END $$;
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("conf_setting", "param_desc")
