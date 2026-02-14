from fastapi import APIRouter, Depends, HTTPException, status, Query
from security.dependencies import get_current_active_user
from typing import List, Annotated
from sqlalchemy.orm import Session

from db import get_db
from dtos.pharmacy.drug import DrugDTO, DrugGroupDTO
from dtos.auth import UserDTO
from repos.pharmacy.drug_group_repository import DrugGroupRepository
from repos.pharmacy.drug_repository import DrugRepository

drug_router = APIRouter(
    prefix="/api/pharmacy/drugs",
    tags=["drugs", "pharmacy"]
)


# Dependency
def get_drug_repository(db: Session = Depends(get_db)):
    return DrugRepository(db)


@drug_router.post("/", status_code=status.HTTP_201_CREATED)
def create_drug(
        drug: DrugDTO,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.create(drug)


@drug_router.get("/")
def read_drugs(
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    drugs = repo.get_all(include_deleted=include_deleted)
    return {'data': drugs[skip: skip + limit], 'total': len(drugs)}


@drug_router.get("/{drug_id}", response_model=DrugDTO)
def read_drug(
        drug_id: int,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    drug = repo.get(drug_id, include_deleted=include_deleted)
    if drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found"
        )
    return drug


@drug_router.put("/{drug_id}", response_model=DrugDTO)
def update_drug(
        drug_id: int,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    drug = repo.get(drug_id)
    db_drug = repo.update(drug_id, drug)
    if db_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found"
        )
    return db_drug


@drug_router.delete("/{drug_id}", response_model=DrugDTO)
def soft_delete_drug(
        drug_id: int,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_drug = repo.soft_delete(drug_id)
    if db_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found"
        )
    return db_drug


@drug_router.post("/{drug_id}/restore", response_model=DrugDTO)
def restore_drug(
        drug_id: int,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_drug = repo.restore(drug_id)
    if db_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found or not deleted"
        )
    return db_drug


@drug_router.get("/search/{name}")
def search_by_name(
        name: str,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):

    return repo.get_by_name(name, include_deleted=include_deleted)


@drug_router.get("/search/manufacturer/{manufacturer}", response_model=List[DrugDTO])
def search_by_manufacturer(
        manufacturer: str,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get_by_manufacturer(manufacturer, include_deleted=include_deleted)


@drug_router.get("/deleted/", response_model=List[DrugDTO])
def get_deleted_drugs(
        repo: DrugRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get_deleted()


def get_drug_repository(db: Session = Depends(get_db)):
    return DrugGroupRepository(db)


@drug_router.get("/groups/")
def get_all_drug_groups(skip: int = Query(0), limit: int = Query(100),
                        repo: DrugGroupRepository = Depends(get_drug_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    """
    Get all drug groups with optional pagination.
    """
    return repo.get_all(skip=skip, limit=limit)
