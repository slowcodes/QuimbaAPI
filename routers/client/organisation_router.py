from typing import Annotated
from fastapi import APIRouter, Depends
from security.dependencies import get_current_active_user
from sqlalchemy.orm import Session

from db import get_db
from dtos.people import OrganisationDTO, OrgType
from dtos.auth import UserDTO
from repos.client.client_repository import ClientRepository
from repos.client.organization_repository import OrganizationRepository

org_router = APIRouter()


def get_org_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    return OrganizationRepository(db)


@org_router.get('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def get_registered_orgs(skip: int = 0, limit: int = 100, org_type: OrgType = OrgType.Others, repo: OrganizationRepository = Depends(get_org_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get_registered_orgs(limit, skip, org_type)


@org_router.post('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def add_registered_orgs(org: OrganisationDTO, repo: OrganizationRepository = Depends(get_org_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.create(org)


@org_router.delete('/apsi/resources/registered-orgs/', tags=['Organization', 'Resources'])
def delete_registered_ord(org: OrganisationDTO, repo: ClientRepository = Depends(get_org_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.delete_registered_org(org)


@org_router.put('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def update_registered_ord(org: OrganisationDTO, repo: OrganizationRepository = Depends(get_org_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.update_registered_org(org)
