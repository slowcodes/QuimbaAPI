"""add soft delete mixin to lab_service

Revision ID: 09dad36ca2fc
Revises: 2fe174056924
Create Date: 2026-01-07 16:57:55.460000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '09dad36ca2fc'
down_revision: Union[str, None] = '2fe174056924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'lab_service',
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('lab_service', 'deleted_at')
