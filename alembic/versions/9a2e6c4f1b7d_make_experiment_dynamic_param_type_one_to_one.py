"""make experiment dynamic param type one to one

Revision ID: 9a2e6c4f1b7d
Revises: 1f6c2b8d4a9e
Create Date: 2026-05-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9a2e6c4f1b7d"
down_revision: Union[str, None] = "1f6c2b8d4a9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_lab_experiment_dynamic_param_type_experiment_id",
        "lab_experiment_dynamic_param_type",
        ["experiment_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_lab_experiment_dynamic_param_type_experiment_id",
        "lab_experiment_dynamic_param_type",
        type_="unique",
    )
