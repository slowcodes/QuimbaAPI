from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from db import get_db
from dtos.auth import UserDTO
from dtos.pharmacy.prescription import PrescriptionDTO
from repos.pharmacy.prescription_repository import PrescriptionRepository
from security.dependencies import get_current_active_user

prescription_router = APIRouter(
    prefix="/api/pharmacy/prescription",
    tags=["prescription", "pharmacy"]
)


# Dependency
def get_prescription_repository(db: Session = Depends(get_db)):
    return PrescriptionRepository(db)


@prescription_router.post("/", response_model=PrescriptionDTO, status_code=status.HTTP_201_CREATED)
def create_prescription(
        prescription: PrescriptionDTO,
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
        repo: PrescriptionRepository = Depends(get_prescription_repository),

):
    return repo.create(prescription, current_user)


@prescription_router.get("/", status_code=status.HTTP_200_OK)
def get_prescription(skip: int = Query(0), limit: int = Query(100),
                     status: str = Query("All"),
                     start_date: str = Query(None),
                     end_date: str = Query(None),
                     repo: PrescriptionRepository = Depends(get_prescription_repository)):
    """
    Get all prescriptions with optional filters and pagination.
    """
    return repo.get_all(skip=skip, limit=limit, status=status, start_date=start_date, end_date=end_date)
