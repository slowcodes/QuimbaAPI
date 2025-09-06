from http.client import HTTPException
from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from dtos.people import ClientDTO, OrganisationDTO, VitalDTO
from sqlalchemy.orm import Session
from db import get_db
from starlette.responses import JSONResponse

from repos.client.vital_rpository import VitalsRepository

vital_router = APIRouter(prefix='/api/clients/vitals', tags=['Clients', 'Vitals'])


def get_vital_repository(db: Session = Depends(get_db)) -> VitalsRepository:
    return VitalsRepository(db)


# @vital_router.get("/", )
# def get_client_vitals(client_id: int,
#                     limit: int = 20,
#                     skip: int = 0,
#                     repo: VitalsRepository = Depends(get_vital_repository)):
#     return repo.get_vitals_by_client_id(skip, limit)


@vital_router.post("/", status_code=status.HTTP_201_CREATED)
def create_vital(vital_dto: VitalDTO, repo: VitalsRepository = Depends(get_vital_repository)):
    """
    Create a new vital record.
    """
    vital = repo.create_vital(vital_dto)
    return status.HTTP_201_CREATED


@vital_router.get("/{vital_id}", response_model=VitalDTO)
def get_vital_by_id(vital_id: int, repo: VitalsRepository = Depends(get_vital_repository)):
    """
    Retrieve a vital record by its ID.
    """
    vital = repo.get_vital_by_id(vital_id)
    if not vital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital not found")
    return vital


@vital_router.get("/")
def get_vitals_by_client_id(
    client_id: int,
    skip: int = 0,
    limit: int = 10,
    vital_type: str = None,
    repo: VitalsRepository = Depends(get_vital_repository),
):
    """
    Retrieve vital records for a specific client with pagination.
    """
    vitals = repo.get_vitals_by_client_id(client_id, skip, limit, vital_type)
    return vitals


@vital_router.put("/{vital_id}", response_model=VitalDTO)
def update_vital(vital_id: int, vital_dto: VitalDTO, repo: VitalsRepository = Depends(get_vital_repository)):
    """
    Update an existing vital record.
    """
    updated_vital = repo.update_vital(vital_id, vital_dto)
    if not updated_vital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital not found")
    return updated_vital


@vital_router.delete("/{vital_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vital(vital_id: int, repo: VitalsRepository = Depends(get_vital_repository)):
    """
    Delete a vital record by its ID.
    """
    is_deleted = repo.delete_vital(vital_id)
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital not found")
    return {"detail": "Vital deleted successfully"}