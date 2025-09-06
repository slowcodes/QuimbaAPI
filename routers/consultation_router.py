from typing import List

from fastapi import APIRouter, HTTPException, Depends, security, Security
from starlette import status

from dtos.consultation import *
from sqlalchemy.orm import Session
from db import get_db
from models.consultation import Specialism
from repos.consultation_repository import ConsultationRepository

consultation_router = APIRouter(prefix="/api/clinicals", tags=["Clinicals"])


def get_consultation_repository(db: Session = Depends(get_db)) -> ConsultationRepository:
    return ConsultationRepository(db)


@consultation_router.get("/symptoms", response_model=List[SymptomDTO], tags=["Symptoms"])
def read_symptoms(repo: ConsultationRepository = Depends(get_consultation_repository)):
    symptoms = repo.get_symptom()
    return symptoms


@consultation_router.get("/consultation/specializations", tags=["Symptoms"])
def read_specializations(skip: int = 0, limit: int = 100,
                         repo: ConsultationRepository = Depends(get_consultation_repository)):
    symptoms = repo.get_specializations(skip=skip, limit=limit)
    return symptoms


@consultation_router.post("/consultation/consultants", response_model=ConsultantDTO, tags=["Consultants"])
def add_consultant(consultant: ConsultantDTO, repo: ConsultationRepository = Depends(get_consultation_repository)):
    """
    Add a new consultant to the system.
    """
    return repo.add_consultant(consultant)


@consultation_router.get("/consultation/consultants", response_model=List[ConsultantDTO], tags=["Consultants"])
def get_consultants(skip: int = 0, limit: int = 100,
                    repo: ConsultationRepository = Depends(get_consultation_repository)):
    """
    Get a list of consultants with optional pagination.
    """
    return repo.get_consultants(skip=skip, limit=limit)


@consultation_router.get("/consultation/consultant/", response_model=ConsultantDTO, tags=["Consultants"])
def get_consultant(id: int, repo: ConsultationRepository = Depends(get_consultation_repository)):
    """
    Get a consultant.
    """
    return repo.get_consultant(id)


@consultation_router.post("/consultation/consultants/inhours", response_model=InHoursDTO)
def add_consulting_hours(in_hours: InHoursDTO,
                         repo: ConsultationRepository = Depends(get_consultation_repository)):
    """
    Add a new consulting hours.
    """
    return repo.addInHours(in_hours)


@consultation_router.get("/consultation/consultants/inhours")
def get_all_consulting_hours(start_time: str, end_time: str, consultant_id: int,
                             repo: ConsultationRepository = Depends(get_consultation_repository)):
    return repo.get_expanded_in_hours(start_time, end_time, consultant_id)


@consultation_router.post("/consultation/consultant/queue/", response_model=ConsultationQueueDTO)
def add_consultation_queue(consultant_queue: ConsultationQueueDTO,
                             repo: ConsultationRepository = Depends(get_consultation_repository)):

    queue = repo.add_consultant_queue(consultant_queue)
    if queue is None:
            raise HTTPException(status_code=404, detail="Booking not found")
    return queue


@consultation_router.get("/consultation/consultant/queue/", response_model=List[ConsultationAppointmentDTO])
def get_consultation_booking(consultant_id: int=0, client_id=0, start_date= '',
                             last_date = '', status:str='', in_hour_id: int = 0, repo: ConsultationRepository = Depends(get_consultation_repository)):

    return repo.get_consultant_queue(
        consultant_id,
        client_id,
        start_date,
        last_date,
        in_hour_id,
        status
    )


# Create Clinical Examination
@consultation_router.post("/clinical_examinations/", response_model=ClinicalExaminationDTO)
def create_clinical_exam(clinical_examination: ClinicalExaminationDTO,
                         repo: ConsultationRepository = Depends(get_consultation_repository)):
    return repo.create_clinical_examination(clinical_examination)


# Get Clinical Examination by ID
@consultation_router.get("/clinical_examinations/{clinical_examination_id}", response_model=ClinicalExaminationDTO)
def read_clinical_examination(clinical_examination_id: int,
                              repo: ConsultationRepository = Depends(get_consultation_repository)):
    db_clinical_examination = repo.get_clinical_examination(clinical_examination_id=clinical_examination_id)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return db_clinical_examination


# Update Clinical Examination
@consultation_router.put("/clinical_examinations/{clinical_examination_id}", response_model=ClinicalExaminationDTO)
def update_clinical_exam(clinical_examination_id: int, clinical_examination: ClinicalExaminationDTO,
                         repo: ConsultationRepository = Depends(get_consultation_repository)):
    db_clinical_examination = repo.update_clinical_examination(clinical_examination_id=clinical_examination_id,
                                                               clinical_examination=clinical_examination)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return db_clinical_examination


# Delete Clinical Examination
@consultation_router.delete("/clinical_examinations/{clinical_examination_id}")
def delete_clinical_examination(clinical_examination_id: int,
                                repo: ConsultationRepository = Depends(get_consultation_repository)):
    db_clinical_examination = repo.delete_clinical_examination(clinical_examination_id=clinical_examination_id)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return {"message": "Clinical Examination deleted successfully"}


