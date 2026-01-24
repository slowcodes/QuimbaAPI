from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dtos.admission import AdmissionCreateDTO, AdmissionDTO, AdmissionUpdateDTO
from repos.admission.admission_repository import AdmissionRepository

admission_router = APIRouter(prefix="/api/admissions", tags=["Admissions"])


def get_admission_repository(db: Session = Depends(get_db)) -> AdmissionRepository:
    return AdmissionRepository(db)


@admission_router.post("/records", response_model=AdmissionDTO, status_code=status.HTTP_201_CREATED)
def create_admission(admission: AdmissionCreateDTO, repo: AdmissionRepository = Depends(get_admission_repository)):
    return repo.create_admission(admission)


@admission_router.get("/records", status_code=status.HTTP_200_OK)
def list_admissions(
    skip: int = 0,
    limit: int = 100,
    patient_id: int = 0,
    repo: AdmissionRepository = Depends(get_admission_repository),
):
    return repo.get_admissions(skip=skip, limit=limit, patient_id=patient_id)


@admission_router.get("/records/{admission_id}", response_model=AdmissionDTO, status_code=status.HTTP_200_OK)
def get_admission(admission_id: int, repo: AdmissionRepository = Depends(get_admission_repository)):
    admission = repo.get_admission(admission_id)
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    return admission


@admission_router.put("/records/{admission_id}", response_model=AdmissionDTO, status_code=status.HTTP_200_OK)
def update_admission(
    admission_id: int,
    admission: AdmissionUpdateDTO,
    repo: AdmissionRepository = Depends(get_admission_repository),
):
    updated = repo.update_admission(admission_id, admission)
    if not updated:
        raise HTTPException(status_code=404, detail="Admission not found")
    return updated


@admission_router.delete("/records/{admission_id}", status_code=status.HTTP_200_OK)
def delete_admission(admission_id: int, repo: AdmissionRepository = Depends(get_admission_repository)):
    deleted = repo.delete_admission(admission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Admission not found")
    return {"deleted": True}
