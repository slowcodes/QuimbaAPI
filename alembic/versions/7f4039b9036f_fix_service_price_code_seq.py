"""fix_service_price_code_seq

Revision ID: 7f4039b9036f
Revises: 09dad36ca2fc
Create Date: 2026-01-09 02:21:26.856335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f4039b9036f'
down_revision: Union[str, None] = '09dad36ca2fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Resync the PostgreSQL sequence for service_price_code.id
    to prevent duplicate primary key violations.
    """
    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('service_price_code', 'id'),
            COALESCE((SELECT MAX(id) FROM service_price_code), 1),
            true
        );
        """
    )


def downgrade() -> None:
    """
    No safe downgrade for sequence realignment.
    Leaving empty intentionally.
    """
    pass