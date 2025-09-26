"""Rebuild sample_type to expanded set

Revision ID: bb4f174ce9a1
Revises: dc8b0053ca78
Create Date: 2025-08-14 12:14:30.598461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'bb4f174ce9a1'
down_revision: Union[str, None] = 'dc8b0053ca78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- CONFIGURE THESE ---
ENUM_NAME = "sampletype"         # the existing type name in PG
AFFECTED = [("lab_collected_sample", "sample_type")]        # list of (table, column) using this enum

OLD_VALUES = (
    "Urine",
    "Feaces",          # typo kept as-is because it's what's in the DB
    "Blood",
    "Skin Swap",
    "Saliva",
)

NEW_VALUES = (
    "Whole blood",
    "Serum",
    "Plasma",
    "Capillary blood",
    "Random urine",
    "First morning urine",
    "Timed urine",
    "Catheterized urine",
    "Stool (fecal)",
    "Throat swabs",
    "Nasal/nasopharyngeal swabs",
    "Wound swabs",
    "Urogenital swabs",
    "Cerebrospinal fluid",
    "Pleural fluid",
    "Peritoneal fluid",
    "Pericardial fluid",
    "Synovial fluid",
    "Bronchoalveolar lavage",
    "Biopsy",
    "Sputum - Mucus from the lungs",
    "Hair",
    "Nail",
    "Amniotic fluid",
    "Saliva",
    "Semen",
    "Tissue",
    "Bone marrow",
    "Breast milk",
)

# temp names for intermediate types
UNION_ENUM_NAME = f"{ENUM_NAME}_union"
NEW_ENUM_NAME = f"{ENUM_NAME}_new"

# choose how to map old -> new; edit to your semantics
OLD_TO_NEW = {
    "Urine": "Random urine",      # or First morning / Timed / Catheterized (you decide)
    "Feaces": "Stool (fecal)",    # fixes spelling and normalizes to Stool
    "Blood": "Whole blood",
    "Skin Swap": "Wound swabs",   # pick the closest category for your app
    # "Saliva" stays the same
}


def _drop_default(table, column):
    """Drop default if the table/column exists."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if table in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns(table)]
        if column in cols:
            op.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" DROP DEFAULT')


def _cast_column(table, column, to_type):
    # cast via text to avoid issues with label reordering
    op.execute(
        f'ALTER TABLE "{table}" '
        f'ALTER COLUMN "{column}" TYPE {to_type} '
        f'USING "{column}"::text::{to_type}'
    )


def upgrade():
    bind = op.get_bind()

    # 1) Create UNION enum (old + new) so all values are valid during transition
    union_values = []
    for v in list(OLD_VALUES) + list(NEW_VALUES):
        if v not in union_values:
            union_values.append(v)
    sa.Enum(*union_values, name=UNION_ENUM_NAME).create(bind, checkfirst=False)

    # 2) Move columns to UNION enum
    for table, col in AFFECTED:
        _drop_default(table, col)
        _cast_column(table, col, UNION_ENUM_NAME)

    # 3) Remap existing rows from old labels -> new labels
    for table, col in AFFECTED:
        # (a) direct replacements
        for old, new in OLD_TO_NEW.items():
            op.execute(
                sa.text(
                    f'UPDATE "{table}" SET "{col}" = :new WHERE "{col}" = :old'
                ).bindparams(new=new, old=old)
            )
        # (b) "Saliva" already exists in NEW_VALUES; nothing to do

    # 4) Create FINAL enum containing only the NEW values
    sa.Enum(*NEW_VALUES, name=NEW_ENUM_NAME).create(bind, checkfirst=False)

    # 5) Cast columns from UNION -> FINAL
    for table, col in AFFECTED:
        _cast_column(table, col, NEW_ENUM_NAME)

    # 6) Swap type names and drop old/union types
    op.execute(f"ALTER TYPE {ENUM_NAME} RENAME TO {ENUM_NAME}_old")
    op.execute(f"ALTER TYPE {NEW_ENUM_NAME} RENAME TO {ENUM_NAME}")
    op.execute(f"DROP TYPE {ENUM_NAME}_old")
    op.execute(f"DROP TYPE {UNION_ENUM_NAME}")


def downgrade():
    """
    Downgrade is lossy because many new labels didn't exist before.
    We collapse new categories back into the old 5 buckets.
    Review this mapping before using downgrade in production.
    """
    bind = op.get_bind()

    # 1) Create UNION (old + new)
    union_values = []
    for v in list(OLD_VALUES) + list(NEW_VALUES):
        if v not in union_values:
            union_values.append(v)
    sa.Enum(*union_values, name=UNION_ENUM_NAME).create(bind, checkfirst=False)

    # 2) Cast columns to UNION so both old/new assignments are allowed
    for table, col in AFFECTED:
        _drop_default(table, col)
        _cast_column(table, col, UNION_ENUM_NAME)

    # 3) Collapse new values back into the old 5
    for table, col in AFFECTED:
        op.execute(
            f'''
            UPDATE "{table}"
            SET "{col}" = CASE
                WHEN "{col}" IN ('Random urine','First morning urine','Timed urine','Catheterized urine') THEN 'Urine'
                WHEN "{col}" IN ('Stool (fecal)') THEN 'Feaces'
                WHEN "{col}" IN ('Throat swabs','Nasal/nasopharyngeal swabs','Wound swabs','Urogenital swabs') THEN 'Skin Swap'
                WHEN "{col}" IN ('Saliva') THEN 'Saliva'
                ELSE 'Blood'  -- catch-all for fluids/tissues (review!)
            END::text::{UNION_ENUM_NAME}
            '''
        )

    # 4) Recreate the OLD 5-value enum and cast back
    old_shape_name = f"{ENUM_NAME}_oldshape"
    sa.Enum(*OLD_VALUES, name=old_shape_name).create(bind, checkfirst=False)

    for table, col in AFFECTED:
        _cast_column(table, col, old_shape_name)

    # 5) Swap names back and drop temps
    op.execute(f"ALTER TYPE {ENUM_NAME} RENAME TO {ENUM_NAME}_newshape")
    op.execute(f"ALTER TYPE {old_shape_name} RENAME TO {ENUM_NAME}")
    op.execute(f"DROP TYPE {ENUM_NAME}_newshape")
    op.execute(f"DROP TYPE {UNION_ENUM_NAME}")
