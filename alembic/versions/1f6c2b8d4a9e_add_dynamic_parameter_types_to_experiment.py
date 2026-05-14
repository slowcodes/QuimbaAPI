"""add dynamic parameter types to experiment

Revision ID: 1f6c2b8d4a9e
Revises: 7d3a9c5e8f1b
Create Date: 2026-05-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "1f6c2b8d4a9e"
down_revision: Union[str, None] = "7d3a9c5e8f1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


dynamic_parameter_type = postgresql.ENUM("Drugs", "Strings", name="dynamicparametertype")


def upgrade() -> None:
    dynamic_parameter_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "lab_experiment",
        sa.Column(
            "use_only_dynamic_param",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("lab_experiment", "use_only_dynamic_param", server_default=None)

    op.create_table(
        "lab_experiment_dynamic_param_type",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=True),
        sa.Column(
            "param_type",
            postgresql.ENUM("Drugs", "Strings", name="dynamicparametertype", create_type=False),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["experiment_id"], ["lab_experiment.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lab_experiment_dynamic_param_type_id"),
        "lab_experiment_dynamic_param_type",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_lab_experiment_dynamic_param_type_id"),
        table_name="lab_experiment_dynamic_param_type",
    )
    op.drop_table("lab_experiment_dynamic_param_type")
    op.drop_column("lab_experiment", "use_only_dynamic_param")
    dynamic_parameter_type.drop(op.get_bind(), checkfirst=True)
