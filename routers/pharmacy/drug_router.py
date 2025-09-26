from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlalchemy.orm import Session

from db import get_db
from dtos.pharmacy.drug import DrugDTO, DrugGroupDTO
from repos.pharmacy.drug_group_repository import DrugGroupRepository
from repos.pharmacy.drug_repository import DrugRepository

drug_router = APIRouter(
    prefix="/api/pharmacy/drugs",
    tags=["drugs", "pharmacy"]
)


# Dependency
def get_drug_repository(db: Session = Depends(get_db)):
    return DrugRepository(db)


@drug_router.post("/", response_model=DrugDTO, status_code=status.HTTP_201_CREATED)
def create_drug(
        drug: DrugDTO,
        repo: DrugRepository = Depends(get_drug_repository)
):
    return repo.create(drug)


@drug_router.get("/")
def read_drugs(
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository)
):
    drugs = repo.get_all(include_deleted=include_deleted)
    return {'data': drugs[skip: skip + limit], 'total': len(drugs)}


@drug_router.get("/{drug_id}", response_model=DrugDTO)
def read_drug(
        drug_id: int,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository)
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
        repo: DrugRepository = Depends(get_drug_repository)
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
        repo: DrugRepository = Depends(get_drug_repository)
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
        repo: DrugRepository = Depends(get_drug_repository)
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
        repo: DrugRepository = Depends(get_drug_repository)
):

    return repo.get_by_name(name, include_deleted=include_deleted)


@drug_router.get("/search/manufacturer/{manufacturer}", response_model=List[DrugDTO])
def search_by_manufacturer(
        manufacturer: str,
        include_deleted: bool = False,
        repo: DrugRepository = Depends(get_drug_repository)
):
    return repo.get_by_manufacturer(manufacturer, include_deleted=include_deleted)


@drug_router.get("/deleted/", response_model=List[DrugDTO])
def get_deleted_drugs(
        repo: DrugRepository = Depends(get_drug_repository)
):
    return repo.get_deleted()


def get_drug_repository(db: Session = Depends(get_db)):
    return DrugGroupRepository(db)


@drug_router.get("/groups/")
def get_all_drug_groups(skip: int = Query(0), limit: int = Query(100),
                        repo: DrugGroupRepository = Depends(get_drug_repository)):
    """
    Get all drug groups with optional pagination.
    """
    return repo.get_all(skip=skip, limit=limit)
