"""add title to person model

Revision ID: 019ae5dc9ee8
Revises: 266dff4824f6
Create Date: 2025-09-01 14:37:49.911436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '019ae5dc9ee8'
down_revision: Union[str, None] = '266dff4824f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    title_enum = sa.Enum('Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Chief', 'Scientist', name='proftitle')
    title_enum.create(op.get_bind(), checkfirst=True)  # create type
    op.add_column("person", sa.Column("title", title_enum, server_default="Mr", nullable=False))


def downgrade() -> None:
    op.drop_column("person", "title")
    title_enum = sa.Enum('Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Chief', 'Scientist', name='proftitle')
    title_enum.drop(op.get_bind(), checkfirst=True)

