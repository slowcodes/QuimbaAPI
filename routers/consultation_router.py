import json
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from cache.redis import get_redis_client
from dtos.auth import UserDTO
from dtos.client.icd10 import Icd10Response
from dtos.consultation import *
from sqlalchemy.orm import Session
from db import get_db
from repos.client.icd10_repository import Icd10Repository
from repos.consultation.clinical_examination_repository import ClinicalExaminationRepository
from repos.consultation.consultant_repository import ConsultantRepository
from repos.consultation.consultation_repository import ConsultationsRepository
from security.dependencies import require_access_privilege

consultation_router = APIRouter(prefix="/api/clinicals", tags=["Clinicals"])


def get_consultation_repository(db: Session = Depends(get_db)) -> ConsultantRepository:
    return ConsultantRepository(db)


def get_icd10_repository(db: Session = Depends(get_db)) -> Icd10Repository:
    return Icd10Repository(db)


@consultation_router.get("/symptoms", response_model=List[SymptomDTO], tags=["Symptoms"])
def read_symptoms(repo: ConsultantRepository = Depends(get_consultation_repository)):
    symptoms = repo.get_symptom()
    return symptoms


@consultation_router.get("/consultation/specializations", tags=["Symptoms"])
def read_specializations(skip: int = 0, limit: int = 100,
                         repo: ConsultantRepository = Depends(get_consultation_repository)):
    symptoms = repo.get_specializations(skip=skip, limit=limit)
    return symptoms


@consultation_router.post("/consultation/consultants", response_model=ConsultantDTO, tags=["Consultants"])
def add_consultant(consultant: ConsultantDTO, repo: ConsultantRepository = Depends(get_consultation_repository)):
    """
    Add a new consultant to the system.
    """
    return repo.add_consultant(consultant)


@consultation_router.put("/consultation/consultants", response_model=ConsultantDTO, tags=["Consultants"])
def update_consultant(consultant: ConsultantDTO, repo: ConsultantRepository = Depends(get_consultation_repository)):
    """
    Update a consultant in the system.
    """
    updated_consultant = repo.update_consultant(consultant.id, consultant)
    if updated_consultant is None:
        raise HTTPException(status_code=404, detail="Consultant not found")
    return updated_consultant


@consultation_router.get("/consultation/consultants", response_model=List[ConsultantDTO], tags=["Consultants"])
def get_consultants(skip: int = 0, limit: int = 100,
                    repo: ConsultantRepository = Depends(get_consultation_repository)):
    """
    Get a list of consultants with optional pagination.
    """
    return repo.get_consultants(skip=skip, limit=limit)


@consultation_router.get("/consultation/consultant/", response_model=ConsultantDTO, tags=["Consultants"])
def get_consultant(id: int, repo: ConsultantRepository = Depends(get_consultation_repository)):
    """
    Get a consultant.
    """
    return repo.get_consultant(id)


@consultation_router.post("/consultation/consultants/inhours", response_model=InHoursDTO)
def add_consulting_hours(in_hours: InHoursDTO,
                         repo: ConsultantRepository = Depends(get_consultation_repository)):
    """
    Add a new consulting hours.
    """
    return repo.addInHours(in_hours)


@consultation_router.get("/consultation/consultants/inhours")
def get_all_consulting_hours(start_time: str, end_time: str, consultant_id: int,
                             repo: ConsultantRepository = Depends(get_consultation_repository)):
    return repo.get_expanded_in_hours(start_time, end_time, consultant_id)


@consultation_router.post("/consultation/consultant/queue/", response_model=ConsultationQueueDTO)
def add_consultation_queue(consultant_queue: ConsultationQueueDTO,
                           repo: ConsultantRepository = Depends(get_consultation_repository)):
    queue = repo.add_consultant_queue(consultant_queue)
    if queue is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return queue


@consultation_router.get("/consultation/icd10/", response_model=Icd10Response)
def get_icd10(skip: int = 0, limit: int = 100,
              repo: Icd10Repository = Depends(get_icd10_repository)):
    queue = repo.list(skip=skip, limit=limit)
    if queue is None:
        raise HTTPException(status_code=404, detail="ICD not found")
    return queue


@consultation_router.get("/consultation/icd10/search/", response_model=Icd10Response)
def search_icd10(keyword: str, skip: int = 0, limit: int = 100,
                 repo: Icd10Repository = Depends(get_icd10_repository)):
    queue = repo.search(keyword, skip=skip, limit=limit)
    if queue is None:
        raise HTTPException(status_code=404, detail="ICD not found")
    return queue


@consultation_router.get("/consultation/consultant/queue/detail/", response_model=ConsultationQueueDTO)
def get_consultation_booking(queue_id: int, refresh: int = 0,
                             repo: ConsultantRepository = Depends(get_consultation_repository)):
    redis = get_redis_client()
    cache_key = f"consultation:{queue_id}"
    cached_consultation = redis.get(cache_key)

    if cached_consultation and refresh == 0:
        consultation = json.loads(cached_consultation.decode("utf-8"))
        print('Consultation is severed from cache')
        return JSONResponse(status_code=status.HTTP_200_OK, content=consultation)

    queue = repo.get_consultation_queue_by_id(queue_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Consultation Booking not found")
    safe_data = jsonable_encoder(queue)
    redis.set(cache_key, json.dumps(safe_data), ex=300)

    return queue


@consultation_router.get("/consultation/consultant/queue/", response_model=List[ConsultationAppointmentDTO])
def get_consultation_booking(consultant_id: int = 0, client_id=0, start_date='',
                             last_date='', xstatus: str = QueueStatus.Processing, in_hour_id: int = 0,
                             repo: ConsultantRepository = Depends(get_consultation_repository)):
    return repo.get_consultant_queue(
        consultant_id,
        client_id,
        start_date,
        last_date,
        in_hour_id,
        xstatus
    )


# Clinical Examination CRUD operations
def get_clinical_examination_repository(db: Session = Depends(get_db)) -> ClinicalExaminationRepository:
    return ClinicalExaminationRepository(db)


# Create Clinical Examination
@consultation_router.post("/clinical_examinations/", response_model=ClinicalExaminationDTO)
def create_clinical_exam(clinical_examination: ClinicalExaminationDTO,
                         repo: ConsultantRepository = Depends(get_clinical_examination_repository)):
    return repo.create(clinical_examination)


# Get Clinical Examination by ID
@consultation_router.get("/clinical_examinations/{clinical_examination_id}", response_model=ClinicalExaminationDTO)
def read_clinical_examination(clinical_examination_id: int,
                              repo: ConsultantRepository = Depends(get_clinical_examination_repository)):
    db_clinical_examination = repo.get_clinical_examination(clinical_examination_id=clinical_examination_id)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return db_clinical_examination


# Update Clinical Examination
@consultation_router.put("/clinical_examinations/{clinical_examination_id}", response_model=ClinicalExaminationDTO)
def update_clinical_exam(clinical_examination_id: int, clinical_examination: ClinicalExaminationDTO,
                         repo: ConsultantRepository = Depends(get_clinical_examination_repository)):
    db_clinical_examination = repo.update_clinical_examination(clinical_examination_id=clinical_examination_id,
                                                               clinical_examination=clinical_examination)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return db_clinical_examination


# Delete Clinical Examination
@consultation_router.delete("/clinical_examinations/{clinical_examination_id}")
def delete_clinical_examination(clinical_examination_id: int,
                                repo: ConsultantRepository = Depends(get_clinical_examination_repository)):
    db_clinical_examination = repo.delete_clinical_examination(clinical_examination_id=clinical_examination_id)
    if db_clinical_examination is None:
        raise HTTPException(status_code=404, detail="Clinical Examination not found")
    return {"message": "Clinical Examination deleted successfully"}


@consultation_router.get("/internal-systems/", response_model=List[str])
def read_internal_systems(repo: ConsultantRepository = Depends(get_consultation_repository)):
    internal_systems = repo.get_internal_systems()
    if internal_systems is None:
        raise HTTPException(status_code=404, detail="Internal not found")
    return internal_systems


# GET all consultations
def get_consultations_repository(db: Session = Depends(get_db)) -> ConsultationsRepository:
    return ConsultationsRepository(db)


@consultation_router.get("/consultation/",
                         response_model=List[ConsultationDTO],
                         tags=["Service", "Consultation"],
                         summary="Get a list of consultations",
                         description="Retrieve paginated service consultation with optional skip and limit"
                         )
def list_consultations(
        repo: ConsultationsRepository = Depends(get_consultations_repository),
        skip: int = 0,
        limit: int = 100,
        client_id: int = 0,
):
    return repo.get_all(skip=skip, limit=limit, client_id=client_id)


# GET a single consultation by ID
@consultation_router.get("/{consultation_id}",
                         tags=["Service", "Consultation"],
                         summary="Get a list of consultations",
                         description="Retrieve consultation by ID",
                         response_model=ConsultationDTO
                         )
def get_consultation(
        consultation_id: int,
        repo: ConsultationsRepository = Depends(get_consultations_repository)
):
    consultation = repo.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    return consultation


# POST create a new consultation
@consultation_router.post("/consultation/",
                          tags=["Service", "Consultation"],
                          summary="Add consultations",
                          description="create consultation record",
                          response_model=ConsultationDTO,
                          status_code=status.HTTP_201_CREATED
                          )
def create_consultation(
        current_user: Annotated[UserDTO, Depends(require_access_privilege(14))],
        consultation_data: ConsultationDetailDTO,
        repo: ConsultationsRepository = Depends(get_consultations_repository)
):
    return repo.create(consultation_data, created_by=current_user)


# put update an existing consultation
@consultation_router.put("/{consultation_id}", response_model=ConsultationDTO)
def update_consultation(
        consultation_id: int,
        consultation_data: ConsultationUpdate,
        repo: ConsultationsRepository = Depends(get_consultations_repository)
):
    updated = repo.update(consultation_id, consultation_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    return updated


# DELETE a consultation
@consultation_router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_consultation(
        consultation_id: int,
        repo: ConsultationsRepository = Depends(get_consultations_repository)
):
    success = repo.delete(consultation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    return None
