from typing import List, Annotated

from fastapi import APIRouter, Depends
from security.dependencies import get_current_active_user
from requests import Session

from db import get_db
from dtos.all import EnumItem
from dtos.auth import UserDTO
from models.product import PackagingType
from repos.product_repository import ProductRepository

product_router = APIRouter(prefix="/api/product", tags=["Product"])


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


@product_router.get("/packaging_types", response_model=List[EnumItem])
def list_packaging_types(
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return [
        EnumItem(key=pt.name, value=pt.value)
        for pt in PackagingType
    ]
