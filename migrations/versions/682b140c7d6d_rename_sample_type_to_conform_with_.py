"""Rename sample_type to conform with python/sqlalchemy conventions 

Revision ID: 682b140c7d6d
Revises: bb4f174ce9a1
Create Date: 2025-08-15 06:49:31.642875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '682b140c7d6d'
down_revision: Union[str, None] = 'bb4f174ce9a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Whole blood' TO 'Whole_Blood'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Capillary blood' TO 'Capillary_Blood'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Random urine' TO 'Random_Urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'First morning urine' TO 'First_Morning_Urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Timed urine' TO 'Timed_Urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Catheterized urine' TO 'Catheterized_Urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Stool (fecal)' TO 'Stool'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Throat swabs' TO 'Throat_Swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Nasal/nasopharyngeal swabs' TO 'Nasal_Nasopharyngeal_Swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Wound swabs' TO 'Wound_Swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Urogenital swabs' TO 'Urogenital_Swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Cerebrospinal fluid' TO 'Cerebrospinal_Fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Pleural fluid' TO 'Pleural_Fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Peritoneal fluid' TO 'Peritoneal_Fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Pericardial fluid' TO 'Pericardial_Fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Synovial fluid' TO 'Synovial_Fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Bronchoalveolar lavage' TO 'Bronchoalveolar_Lavage'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Biopsy' TO 'biopsy'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Sputum - Mucus from the lungs' TO 'Sputum'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Amniotic fluid' TO 'Amniotic_Fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Bone marrow' TO 'Bone_Marrow'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Breast milk' TO 'Breast_Milk'")


def downgrade():
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Whole_Blood' TO 'Whole blood'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Capillary_Blood' TO 'Capillary blood'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Random_Urine' TO 'Random urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'First_Morning_Urine' TO 'First morning urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Timed_Urine' TO 'Timed urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Catheterized_Urine' TO 'Catheterized urine'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Stool' TO 'Stool (fecal)'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Throat_Swabs' TO 'Throat swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Nasal_Nasopharyngeal_Swabs' TO 'Nasal/nasopharyngeal swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Wound_Swabs' TO 'Wound swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Urogenital_Swabs' TO 'Urogenital swabs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Cerebrospinal_Fluid' TO 'Cerebrospinal fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Pleural_Fluid' TO 'Pleural fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Peritoneal_Fluid' TO 'Peritoneal fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Pericardial_Fluid' TO 'Pericardial fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Synovial_Fluid' TO 'Synovial fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Bronchoalveolar_Lavage' TO 'Bronchoalveolar lavage'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'biopsy' TO 'Biopsy'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Sputum' TO 'Sputum - Mucus from the lungs'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Amniotic_Fluid' TO 'Amniotic fluid'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Bone_Marrow' TO 'Bone marrow'")
    op.execute("ALTER TYPE sampletype RENAME VALUE 'Breast_Milk' TO 'Breast milk'")
