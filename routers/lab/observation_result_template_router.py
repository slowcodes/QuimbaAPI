from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dtos.auth import UserDTO
from dtos.lab import (
    LabObservationResultTemplateCreateDTO,
    LabObservationResultTemplateDTO,
    LabObservationResultTemplateUpdateDTO,
)
from repos.lab.observation_result_template_repository import (
    LabObservationResultTemplateRepository,
)
from security.dependencies import get_current_active_user


observation_result_template_router = APIRouter(
    prefix="/api/laboratories/observation-result-templates",
    tags=["Laboratories", "Observation Result Templates"],
)


def get_observation_result_template_repository(
    db: Session = Depends(get_db),
) -> LabObservationResultTemplateRepository:
    return LabObservationResultTemplateRepository(db)


@observation_result_template_router.post(
    "/",
    response_model=LabObservationResultTemplateDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_observation_result_template(
    template: LabObservationResultTemplateCreateDTO,
    repo: LabObservationResultTemplateRepository = Depends(
        get_observation_result_template_repository
    ),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    return repo.create_template(template, created_by=current_user.id)


@observation_result_template_router.get("/", status_code=status.HTTP_200_OK)
def list_observation_result_templates(
    skip: int = 0,
    limit: int = 100,
    search_text: str = "",
    repo: LabObservationResultTemplateRepository = Depends(
        get_observation_result_template_repository
    ),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    return repo.get_templates(skip=skip, limit=limit, search_text=search_text)


@observation_result_template_router.get("/search", status_code=status.HTTP_200_OK)
def search_observation_result_templates(
    search_text: str,
    skip: int = 0,
    limit: int = 100,
    repo: LabObservationResultTemplateRepository = Depends(
        get_observation_result_template_repository
    ),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    return repo.search_templates(search_text=search_text, skip=skip, limit=limit)


@observation_result_template_router.get(
    "/{template_id}",
    response_model=LabObservationResultTemplateDTO,
    status_code=status.HTTP_200_OK,
)
def get_observation_result_template(
    template_id: int,
    repo: LabObservationResultTemplateRepository = Depends(
        get_observation_result_template_repository
    ),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    template = repo.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Observation result template not found")
    return template


@observation_result_template_router.put(
    "/{template_id}",
    response_model=LabObservationResultTemplateDTO,
    status_code=status.HTTP_200_OK,
)
def update_observation_result_template(
    template_id: int,
    template: LabObservationResultTemplateUpdateDTO,
    repo: LabObservationResultTemplateRepository = Depends(
        get_observation_result_template_repository
    ),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    updated = repo.update_template(template_id, template)
    if not updated:
        raise HTTPException(status_code=404, detail="Observation result template not found")
    return updated


@observation_result_template_router.delete(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
)
def delete_observation_result_template(
    template_id: int,
    repo: LabObservationResultTemplateRepository = Depends(
        get_observation_result_template_repository
    ),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    deleted = repo.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Observation result template not found")
    return {"deleted": True}
