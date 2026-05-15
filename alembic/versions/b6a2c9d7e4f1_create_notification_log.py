"""create notification log

Revision ID: b6a2c9d7e4f1
Revises: 8f2c1d7e4a6b
Create Date: 2026-05-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b6a2c9d7e4f1"
down_revision: Union[str, None] = "8f2c1d7e4a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


notification_log_status = postgresql.ENUM(
    "Success",
    "Failure",
    "Pending",
    name="notification_log_status",
    create_type=False,
)
notification_message_type = postgresql.ENUM(
    "Result",
    "Enrollment",
    "Appointment",
    "Reminder",
    name="notification_message_type",
    create_type=False,
)
notification_channel = postgresql.ENUM(
    "Email",
    "WhatsApp",
    "SMS",
    name="notification_channel",
    create_type=False,
)
notification_log_type = postgresql.ENUM(
    "Notification",
    name="notification_log_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    notification_log_status.create(bind, checkfirst=True)
    notification_message_type.create(bind, checkfirst=True)
    notification_channel.create(bind, checkfirst=True)
    notification_log_type.create(bind, checkfirst=True)

    op.create_table(
        "notification_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status", notification_log_status, nullable=True),
        sa.Column("message_type", notification_message_type, nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("log_type", notification_log_type, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transaction.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notification_log_id"), "notification_log", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_log_id"), table_name="notification_log")
    op.drop_table("notification_log")

    bind = op.get_bind()
    notification_log_type.drop(bind, checkfirst=True)
    notification_channel.drop(bind, checkfirst=True)
    notification_message_type.drop(bind, checkfirst=True)
    notification_log_status.drop(bind, checkfirst=True)
