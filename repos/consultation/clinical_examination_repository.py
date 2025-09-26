from sqlalchemy.orm import Session

from dtos.consultation import ClinicalExaminationDTO
from models.consultation import ClinicalExamination


class ClinicalExaminationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, clinical_examination_data: ClinicalExaminationDTO) -> ClinicalExaminationDTO:
        db_clinical_examination = ClinicalExamination(**clinical_examination_data.dict())
        self.db.add(db_clinical_examination)
        self.db.commit()
        self.db.refresh(db_clinical_examination)
        return ClinicalExaminationDTO(**db_clinical_examination.__dict__)
