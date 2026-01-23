from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dtos.admission import BedCreateDTO, BedDTO, BedUpdateDTO
from repos.admission.bed_repository import BedRepository

bed_router = APIRouter(prefix="/api/admissions", tags=["Admissions"])


def get_bed_repository(db: Session = Depends(get_db)) -> BedRepository:
    return BedRepository(db)


@bed_router.post("/beds", response_model=BedDTO, status_code=status.HTTP_201_CREATED)
def create_bed(bed: BedCreateDTO, repo: BedRepository = Depends(get_bed_repository)):
    return repo.create_bed(bed)


@bed_router.get("/beds", status_code=status.HTTP_200_OK)
def list_beds(skip: int = 0, limit: int = 100, ward_id: int = 0, repo: BedRepository = Depends(get_bed_repository)):
    return repo.get_beds(skip=skip, limit=limit, ward_id=ward_id)


@bed_router.get("/beds/{bed_id}", response_model=BedDTO, status_code=status.HTTP_200_OK)
def get_bed(bed_id: int, repo: BedRepository = Depends(get_bed_repository)):
    bed = repo.get_bed(bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed


@bed_router.put("/beds/{bed_id}", response_model=BedDTO, status_code=status.HTTP_200_OK)
def update_bed(bed_id: int, bed: BedUpdateDTO, repo: BedRepository = Depends(get_bed_repository)):
    updated = repo.update_bed(bed_id, bed)
    if not updated:
        raise HTTPException(status_code=404, detail="Bed not found")
    return updated


@bed_router.delete("/beds/{bed_id}", status_code=status.HTTP_200_OK)
def delete_bed(bed_id: int, repo: BedRepository = Depends(get_bed_repository)):
    deleted = repo.delete_bed(bed_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bed not found")
    return {"deleted": True}
