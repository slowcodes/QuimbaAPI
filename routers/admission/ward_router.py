from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from security.dependencies import get_current_active_user
from sqlalchemy.orm import Session

from db import get_db
from dtos.admission import WardCreateDTO, WardDTO, WardUpdateDTO
from dtos.auth import UserDTO
from repos.admission.ward_repository import WardRepository

ward_router = APIRouter(prefix="/api/admissions", tags=["Admissions"])


def get_ward_repository(db: Session = Depends(get_db)) -> WardRepository:
    return WardRepository(db)


@ward_router.post("/wards", response_model=WardDTO, status_code=status.HTTP_201_CREATED)
def create_ward(ward: WardCreateDTO, repo: WardRepository = Depends(get_ward_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.create_ward(ward)


@ward_router.get("/wards", status_code=status.HTTP_200_OK)
def list_wards(skip: int = 0, limit: int = 100, repo: WardRepository = Depends(get_ward_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get_wards(skip=skip, limit=limit)


@ward_router.get("/wards/{ward_id}", response_model=WardDTO, status_code=status.HTTP_200_OK)
def get_ward(ward_id: int, repo: WardRepository = Depends(get_ward_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    ward = repo.get_ward(ward_id)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return ward


@ward_router.put("/wards/{ward_id}", response_model=WardDTO, status_code=status.HTTP_200_OK)
def update_ward(ward_id: int, ward: WardUpdateDTO, repo: WardRepository = Depends(get_ward_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    updated = repo.update_ward(ward_id, ward)
    if not updated:
        raise HTTPException(status_code=404, detail="Ward not found")
    return updated


@ward_router.delete("/wards/{ward_id}", status_code=status.HTTP_200_OK)
def delete_ward(ward_id: int, repo: WardRepository = Depends(get_ward_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    deleted = repo.delete_ward(ward_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ward not found")
    return {"deleted": True}
