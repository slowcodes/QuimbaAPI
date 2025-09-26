from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from db import get_db
from dtos.auth import UserDTO
from dtos.supply import SupplyDTO
from repos.supply_repository import SupplyRepository
from security.dependencies import get_current_active_user

supply_router = APIRouter(prefix="/api/supply", tags=["Supply"])


def supply_repository(db: Session = Depends(get_db)):
    return SupplyRepository(db)


@supply_router.post("/", status_code=status.HTTP_201_CREATED)
def create_supply(
    # current_user: Annotated[UserDTO, Depends(get_current_active_user())],
    supply: SupplyDTO, repo: SupplyRepository = Depends(supply_repository),
                  ):
    instock = repo.process_supply(supply)
    return supply


@supply_router.post("/inventory", status_code=status.HTTP_201_CREATED)
def pharmacy_inventory(
        skip: int, limit: int, repo: SupplyRepository = Depends(supply_repository)):

    return []