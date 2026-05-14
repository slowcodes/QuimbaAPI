from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from security.dependencies import get_current_active_user
from starlette import status

from db import get_db
from sqlalchemy.orm import Session

from dtos.services import BusinessServiceDTO
from dtos.auth import UserDTO
from repos.services.business_service_repository import BusinessServiceRepository

business_service_router = APIRouter(prefix="/api/v1/business-service", tags=["Service Bookings"])


def service_repository(db: Session = Depends(get_db)):
    return BusinessServiceRepository(db)


@business_service_router.get("/{service_id}", response_model=BusinessServiceDTO)
def get_service(service_id: int, repo: BusinessServiceRepository = Depends(service_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    service = repo.get_by_id(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service
