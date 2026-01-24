from typing import Optional

from sqlalchemy.orm import Session, joinedload

from dtos.admission import AdmissionCreateDTO, AdmissionDTO, AdmissionUpdateDTO
from models.admission import Admission


class AdmissionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_admission(self, admission: AdmissionCreateDTO) -> AdmissionDTO:
        db_admission = Admission(**admission.dict())
        self.session.add(db_admission)
        self.session.commit()
        self.session.refresh(db_admission)
        return AdmissionDTO.from_orm(db_admission)

    def get_admission(self, admission_id: int) -> Optional[AdmissionDTO]:
        admission = (
            self.session.query(Admission)
            .options(joinedload(Admission.bed), joinedload(Admission.user))
            .filter(Admission.id == admission_id)
            .first()
        )
        return AdmissionDTO.from_orm(admission) if admission else None

    def get_admissions(self, skip: int = 0, limit: int = 100, patient_id: int = 0) -> dict:
        query = self.session.query(Admission).options(
            joinedload(Admission.bed),
            joinedload(Admission.user),
        )
        if patient_id:
            query = query.filter(Admission.patient_id == patient_id)
        total = query.count()
        admissions = query.offset(skip).limit(limit).all()
        return {
            "data": [AdmissionDTO.from_orm(admission) for admission in admissions],
            "total": total,
        }

    def update_admission(self, admission_id: int, admission_update: AdmissionUpdateDTO) -> Optional[AdmissionDTO]:
        admission = self.session.query(Admission).filter(Admission.id == admission_id).first()
        if not admission:
            return None
        for key, value in admission_update.dict(exclude_unset=True).items():
            setattr(admission, key, value)
        self.session.commit()
        self.session.refresh(admission)
        return AdmissionDTO.from_orm(admission)

    def delete_admission(self, admission_id: int) -> bool:
        admission = self.session.query(Admission).filter(Admission.id == admission_id).first()
        if not admission:
            return False
        self.session.delete(admission)
        self.session.commit()
        return True
