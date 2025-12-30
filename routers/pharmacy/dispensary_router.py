from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from starlette import status

from db import get_db
from dtos.auth import UserDTO
from dtos.pharmacy.dispensed import DispensedPrescriptionRead, DispensedPrescriptionCreate
from repos.pharmacy.dispensed_drugs import DispensedDrugRepository
from security.dependencies import get_current_active_user

dispensary_router = APIRouter(
    prefix="/api/pharmacy/dispensary",
    tags=["drugs", "pharmacy"]
)


def get_dispensary_repository(db: Session = Depends(get_db)) -> DispensedDrugRepository:
    return DispensedDrugRepository(db)


@dispensary_router.get("/", response_model=List[DispensedPrescriptionRead])
def read_dispensed_drugs(
        skip: int = 0,
        limit: int = 10,
        client_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        last_date: Optional[datetime] = None,
        repo: DispensedDrugRepository = Depends(get_dispensary_repository)
):
    return repo.get_dispensed_drugs(
        skip=skip,
        limit=limit,
        start_date=start_date,
        last_date=last_date,
    )


@dispensary_router.get("/prescription/dispensed/")
def get_dispensed_prescription(skip: int = 0,
                               limit: int = 10,
                               client_id: Optional[int] = None,
                               start_date: Optional[datetime] = None,
                               last_date: Optional[datetime] = None,
                               repo: DispensedDrugRepository = Depends(get_dispensary_repository)
                               ):
    return repo.get_dispensed_prescription(
        client_id=client_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        last_date=last_date,
    )


@dispensary_router.post("/", response_model=DispensedPrescriptionRead, status_code=status.HTTP_201_CREATED)
def create_dispensed_prescription(
        payload: DispensedPrescriptionCreate,
        repo: DispensedDrugRepository = Depends(get_dispensary_repository)
):
    try:
        new_entry = repo.create(payload.dict())
        return new_entry
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"Error creating record: {str(e)}")
