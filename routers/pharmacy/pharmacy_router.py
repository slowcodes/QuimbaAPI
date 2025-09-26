from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlalchemy.orm import Session

from db import get_db
from repos.pharmacy.drug_group_repository import DrugGroupRepository
from repos.supply_repository import SupplyRepository

pharmacy_router = APIRouter(
    prefix="/api/pharmacy",
    tags=["drugs", "pharmacy"]
)


# Dependency
def get_supply_repository(db: Session = Depends(get_db)):
    return SupplyRepository(db)


@pharmacy_router.get("/stock/")
def get_all_drug_groups(skip: int = Query(0), limit: int = Query(100),
                        repo: SupplyRepository = Depends(get_supply_repository)):
    """
    Get all drug groups with optional pagination.
    """
    return repo.pharmacy_inventory(skip=skip, limit=limit)
