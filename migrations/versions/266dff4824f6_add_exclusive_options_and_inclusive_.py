"""Add Exclusive_Options and Inclusive_Options to parameter_type_enum

Revision ID: 266dff4824f6
Revises: 682b140c7d6d
Create Date: 2025-08-23 02:00:30.437754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '266dff4824f6'
down_revision: Union[str, None] = '682b140c7d6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE parametertype ADD VALUE IF NOT EXISTS 'Exclusive_Options'")
    op.execute("ALTER TYPE parametertype ADD VALUE IF NOT EXISTS 'Inclusive_Options'")


def downgrade() -> None:
    # Postgres does NOT support removing enum values directly.
    # To downgrade safely, we must recreate the old type without the new values.
    op.execute("ALTER TYPE parametertype RENAME TO parametertypeold")
    op.execute("CREATE TYPE parametertype AS ENUM ('Number', 'Ratio', 'Description')")
    op.execute("""
        ALTER TABLE lab_experiment_parameter
        ALTER COLUMN parameter_type TYPE parametertype
        USING parameter_type::text::parametertype
    """)
    op.execute("DROP TYPE parametertypeold")
