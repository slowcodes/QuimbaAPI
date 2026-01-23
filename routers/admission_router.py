from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dtos.admission import WardCreateDTO, WardDTO, WardUpdateDTO
from repos.admission_repository import WardRepository

admission_router = APIRouter(prefix="/api/admissions", tags=["Admissions"])


def get_ward_repository(db: Session = Depends(get_db)) -> WardRepository:
    return WardRepository(db)


@admission_router.post("/wards", response_model=WardDTO, status_code=status.HTTP_201_CREATED)
def create_ward(ward: WardCreateDTO, repo: WardRepository = Depends(get_ward_repository)):
    return repo.create_ward(ward)


@admission_router.get("/wards", status_code=status.HTTP_200_OK)
def list_wards(skip: int = 0, limit: int = 100, repo: WardRepository = Depends(get_ward_repository)):
    return repo.get_wards(skip=skip, limit=limit)


@admission_router.get("/wards/{ward_id}", response_model=WardDTO, status_code=status.HTTP_200_OK)
def get_ward(ward_id: int, repo: WardRepository = Depends(get_ward_repository)):
    ward = repo.get_ward(ward_id)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return ward


@admission_router.put("/wards/{ward_id}", response_model=WardDTO, status_code=status.HTTP_200_OK)
def update_ward(ward_id: int, ward: WardUpdateDTO, repo: WardRepository = Depends(get_ward_repository)):
    updated = repo.update_ward(ward_id, ward)
    if not updated:
        raise HTTPException(status_code=404, detail="Ward not found")
    return updated


@admission_router.delete("/wards/{ward_id}", status_code=status.HTTP_200_OK)
def delete_ward(ward_id: int, repo: WardRepository = Depends(get_ward_repository)):
    deleted = repo.delete_ward(ward_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ward not found")
    return {"deleted": True}
