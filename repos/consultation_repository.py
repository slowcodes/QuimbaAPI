from typing import List, Optional
from sqlalchemy.orm import Session
from commands.consultation import SymptomDTO, ClinicalExaminationDTO, PresentingSymptomDTO
from models.consultation import Symptom, ClinicalExamination, PresentingSymptom


def get_symptom(db: Session) -> List[SymptomDTO]:
    symptoms = db.query(Symptom).all()
    return [SymptomDTO(symptom=symptom.symptom, id=symptom.id) for symptom in symptoms]


def create_clinical_examination(db: Session,
                                clinical_examination_data: ClinicalExaminationDTO) -> ClinicalExaminationDTO:
    db_clinical_examination = ClinicalExamination(**clinical_examination_data.dict())
    db.add(db_clinical_examination)
    db.commit()
    db.refresh(db_clinical_examination)
    return ClinicalExaminationDTO(**db_clinical_examination.__dict__)


def get_clinical_examination(db: Session, clinical_examination_id: int) -> ClinicalExaminationDTO:
    db_clinical_examination = db.query(ClinicalExamination).filter(
        ClinicalExamination.id == clinical_examination_id).first()
    return ClinicalExaminationDTO(**db_clinical_examination.__dict__) if db_clinical_examination else None


def update_clinical_examination(db: Session, db_clinical_examination: ClinicalExamination,
                                clinical_examination_data: ClinicalExaminationDTO) -> ClinicalExaminationDTO:
    for field, value in clinical_examination_data.dict().items():
        setattr(db_clinical_examination, field, value)
    db.commit()
    db.refresh(db_clinical_examination)
    return ClinicalExaminationDTO(**db_clinical_examination.__dict__)


def create_presenting_symptom(db: Session, presenting_symptom_data: PresentingSymptomDTO) -> PresentingSymptomDTO:
    db_presenting_symptom = PresentingSymptom(**presenting_symptom_data.dict())
    db.add(db_presenting_symptom)
    db.commit()
    db.refresh(db_presenting_symptom)
    return PresentingSymptomDTO(**db_presenting_symptom.__dict__)


def get_presenting_symptom(db: Session, presenting_symptom_id: int) -> PresentingSymptomDTO:
    db_presenting_symptom = db.query(PresentingSymptom).filter(PresentingSymptom.id == presenting_symptom_id).first()
    return PresentingSymptomDTO(**db_presenting_symptom.__dict__) if db_presenting_symptom else None


def update_presenting_symptom(db: Session, db_presenting_symptom: PresentingSymptom,
                              presenting_symptom_data: PresentingSymptomDTO) -> PresentingSymptomDTO:
    for field, value in presenting_symptom_data.dict().items():
        setattr(db_presenting_symptom, field, value)
    db.commit()
    db.refresh(db_presenting_symptom)
    return PresentingSymptomDTO(**db_presenting_symptom.__dict__)


# PresentingSymptom Repository
def create_presenting_symptom(db: Session, presenting_symptom: PresentingSymptomDTO) -> ClinicalExaminationDTO:
    db_presenting_symptom = PresentingSymptom(**presenting_symptom.dict())
    db.add(db_presenting_symptom)
    db.commit()
    db.refresh(db_presenting_symptom)
    return {
        'id':db_presenting_symptom.id,
        'severity':db_presenting_symptom.severity,
        'frequency':db_presenting_symptom.frequency,
        'symptom_id': db_presenting_symptom.symptom_id,
        'clinical_examination_id':db_presenting_symptom.clinical_examination_id
    }


# ClinicalExamination Repository
def create_clinical_examination(db: Session, clinical_examination: ClinicalExaminationDTO) -> ClinicalExaminationDTO:
    # db_clinical_examination = ClinicalExamination(**clinical_examination.dict())
    db_clinical_examination = ClinicalExamination(
        presenting_complaints=clinical_examination.presenting_complaints,
        transaction_id=clinical_examination.transaction_id,
        conducted_by=1
    )
    db.add(db_clinical_examination)
    db.commit()
    db.refresh(db_clinical_examination)

    sym: List[PresentingSymptomDTO] = []
    for symp in clinical_examination.symptoms:
        sym.append(
            create_presenting_symptom(db,
                                      PresentingSymptomDTO(
                                          symptom_id=symp.symptom_id,
                                          clinical_examination_id=db_clinical_examination.id,
                                          severity=symp.severity,
                                          frequency=symp.frequency
                                      )
                                    )
        )

    return {
        'id': db_clinical_examination.id,
        'transaction_id': db_clinical_examination.transaction_id,
        'conducted_by': db_clinical_examination.conducted_by,
        'symptoms': sym,
        'conducted_at': db_clinical_examination.conducted_at,
        'presenting_complaints': db_clinical_examination.presenting_complaints
    }


# Get Clinical Examination by ID
def get_clinical_examination(db: Session, clinical_examination_id: int) -> Optional[ClinicalExamination]:
    return db.query(ClinicalExamination).filter(ClinicalExamination.id == clinical_examination_id).first()


# Update Clinical Examination
def update_clinical_examination(db: Session, clinical_examination_id: int,
                                clinical_examination: ClinicalExaminationDTO) -> Optional[ClinicalExaminationDTO]:
    db_clinical_examination = db.query(ClinicalExamination).filter(
        ClinicalExamination.id == clinical_examination_id).first()
    if db_clinical_examination:
        update_data = clinical_examination.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_clinical_examination, key, value)
        db.commit()
        db.refresh(db_clinical_examination)
    return db_clinical_examination


# Delete Clinical Examination
def delete_clinical_examination(db: Session, clinical_examination_id: int) -> Optional[ClinicalExaminationDTO]:
    db_clinical_examination = db.query(ClinicalExamination).filter(
        ClinicalExamination.id == clinical_examination_id).first()
    if db_clinical_examination:
        db.delete(db_clinical_examination)
        db.commit()
    return db_clinical_examination
