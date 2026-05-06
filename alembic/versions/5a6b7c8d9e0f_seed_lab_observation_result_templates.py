"""seed lab observation result templates

Revision ID: 5a6b7c8d9e0f
Revises: 4c9d2e7a1b5f
Create Date: 2026-05-06 00:00:00.000000
"""
import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a6b7c8d9e0f"
down_revision: Union[str, None] = "4c9d2e7a1b5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TEMPLATE_DESC = "Complete blood count observation"


def upgrade() -> None:
    seed_time = datetime.datetime(2026, 5, 6)
    templates_table = sa.table(
        "lab_observation_result_template",
        sa.column("template", sa.Text),
        sa.column("template_desc", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("created_by", sa.Integer),
    )

    op.bulk_insert(
        templates_table,
        [
            {
                "template_desc": TEMPLATE_DESC,
                "template": (
                    "CBC findings reviewed. Hemoglobin, total white cell count, "
                    "differential count, and platelet count are documented above. "
                    "Correlate with clinical findings."
                ),
                "created_at": seed_time,
                "created_by": 1,
            },
        ],
    )


def downgrade() -> None:
    seed_time = datetime.datetime(2026, 5, 6)
    templates_table = sa.table(
        "lab_observation_result_template",
        sa.column("template_desc", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("created_by", sa.Integer),
    )
    op.execute(
        templates_table.delete().where(
            sa.and_(
                templates_table.c.template_desc == TEMPLATE_DESC,
                templates_table.c.created_at == seed_time,
                templates_table.c.created_by == 1,
            )
        )
    )
