from fastapi import APIRouter, Depends, HTTPException, status, Query
from security.dependencies import get_current_active_user
from typing import List, Annotated
from sqlalchemy.orm import Session

from db import get_db
from dtos.sales import BusinessSalesRead, BusinessSalesCreate
from dtos.auth import UserDTO
from repos.pharmacy.drug_group_repository import DrugGroupRepository
from repos.sale_repository import SaleRepository
from repos.supply_repository import SupplyRepository

sales_router = APIRouter(
    prefix="/api/sales",
    tags=["dispensaries", "pharmacy" "sales"]
)


# Dependency
def get_sale_repository(db: Session = Depends(get_db)):
    return SaleRepository(db)


@sales_router.post("/", response_model=BusinessSalesRead, status_code=status.HTTP_201_CREATED)
def create_business_sale(
    sale_data: BusinessSalesCreate,
    repo: SaleRepository = Depends(get_sale_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    """
    Create a new business sale record.
    """
    try:
        new_sale = repo.create(sale_data.dict())
        return new_sale
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create sale: {str(e)}"
        )