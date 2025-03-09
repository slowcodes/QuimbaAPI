from typing import List

from fastapi import APIRouter, HTTPException, Depends, security, Security
from starlette import status

from commands.consultation import *
from sqlalchemy.orm import Session
from db import get_db
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from repos import consultation_repository
from repos.consultation_repository import get_symptom, create_clinical_examination, update_clinical_examination, get_clinical_examination

consultation_router = APIRouter(prefix="/api/clinicals", tags=["Clinicals"])


@consultation_router.get("/symptoms", response_model=List[SymptomDTO], tags=["Symptoms"])
def read_symptoms(db: Session = Depends(get_db)):
    symptoms = get_symptom(db)
    return symptoms


# Create Clinical Examination
@consultation_router.post("/clinical_examinations/", response_model=ClinicalExaminationDTO)
def create_clinical_exam(clinical_examination: ClinicalExaminationDTO, db: Session = Depends(get_db)):
    return create_clinical_examination(db, clinical_examination)


# Get Clinical Examination by ID
@consultation_router.get("/clinical_examinations/{clinical_examination_id}", response_model=ClinicalExaminationDTO)
def read_clinical_examination(clinical_examination_id: int, db: Session = Depends(get_db)):
    db_clinical_examination = get_clinical_examination(db, clinical_examination_id=clinical_examination_id)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return db_clinical_examination


# Update Clinical Examination
@consultation_router.put("/clinical_examinations/{clinical_examination_id}", response_model=ClinicalExaminationDTO)
def update_clinical_exam(clinical_examination_id: int, clinical_examination: ClinicalExaminationDTO,
                                db: Session = Depends(get_db)):
    db_clinical_examination = update_clinical_examination(db=db, clinical_examination_id=clinical_examination_id,
                                                          clinical_examination=clinical_examination)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return db_clinical_examination


# Delete Clinical Examination
@consultation_router.delete("/clinical_examinations/{clinical_examination_id}")
def delete_clinical_examination(clinical_examination_id: int, db: Session = Depends(get_db)):
    db_clinical_examination = delete_clinical_examination(db=db, clinical_examination_id=clinical_examination_id)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return {"message": "Clinical Examination deleted successfully"}
