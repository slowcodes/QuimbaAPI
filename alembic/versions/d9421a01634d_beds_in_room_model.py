"""beds in room model

Revision ID: d9421a01634d
Revises: ccda595c2f5f
Create Date: 2026-01-24 01:18:39.010950
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d9421a01634d"
down_revision: Union[str, None] = "ccda595c2f5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "admission_ward_room",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ward_id", sa.Integer(), nullable=True),
        sa.Column("room_number", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column(
            "status",
            sa.Enum("Occupied", "Free", "Maintenance", name="bedroomstatus"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["ward_id"], ["admission_ward.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admission_ward_room_id"), "admission_ward_room", ["id"], unique=False)

    op.create_table(
        "admission_bed_in_rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=True),
        sa.Column("bed_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["bed_id"], ["admission_bed.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["room_id"], ["admission_ward_room.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admission_bed_in_rooms_id"), "admission_bed_in_rooms", ["id"], unique=False)

    op.add_column("admission", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "admission", "admission_bed", ["bed_id"], ["id"], ondelete="cascade")
    op.create_foreign_key(None, "admission", "users", ["user_id"], ["id"], ondelete="cascade")
    op.drop_column("admission", "ward_id")

    op.add_column("admission_bed", sa.Column("bed_number", sa.String(length=50), nullable=False))
    op.add_column(
        "admission_bed",
        sa.Column("status", sa.Enum("Occupied", "Free", "Maintenance", name="bedroomstatus"), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("admission_bed", "status")
    op.drop_column("admission_bed", "bed_number")

    op.add_column("admission", sa.Column("ward_id", sa.Integer(), autoincrement=False, nullable=True))
    op.drop_constraint(None, "admission", type_="foreignkey")
    op.drop_constraint(None, "admission", type_="foreignkey")
    op.drop_column("admission", "user_id")

    op.drop_index(op.f("ix_admission_bed_in_rooms_id"), table_name="admission_bed_in_rooms")
    op.drop_table("admission_bed_in_rooms")
    op.drop_index(op.f("ix_admission_ward_room_id"), table_name="admission_ward_room")
    op.drop_table("admission_ward_room")
