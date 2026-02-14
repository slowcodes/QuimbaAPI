from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status
from security.dependencies import get_current_active_user

from dtos.people import ReferralDTO, PersonDTO, OrganisationDTO, ReferralResponseDTO
from dtos.auth import UserDTO
from db import get_db
from sqlalchemy.orm import Session

from repos.client.organization_repository import OrganizationRepository, OrganizationPeopleRepository
from repos.client.person_repository import PersonRepository
from repos.client.referral_repository import ReferralRepository

referral_router = APIRouter(prefix='/api/clients/referral', tags=['Clients', 'Referral'])


def get_referral_repository(db: Session = Depends(get_db)) -> ReferralRepository:
    return ReferralRepository(db)


def get_people_repository(db: Session = Depends(get_db)) -> PersonRepository:
    return PersonRepository(db)


def get_organization_people_repository(db: Session = Depends(get_db)) -> OrganizationPeopleRepository:
    return OrganizationPeopleRepository(db)


def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    return OrganizationRepository(db)


@referral_router.post("/")
def create_referral(referral: ReferralDTO,
                    repo: ReferralRepository = Depends(get_referral_repository),
                    people_repo: PersonRepository = Depends(get_people_repository),
                    org_repo: OrganizationRepository = Depends(get_organization_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    """Creates a referral by checking if person and organization exist."""

    # Check if person already exists by email or phone
    person_exists = people_repo.person_exists(referral.person)

    # Check if organization exists by email or phone

    # If either person or organization exists, raise an error
    if person_exists:
        raise HTTPException(400, "Person or organization exist")

    # Create person if they don't exist
    new_person = people_repo.create(referral.person)
    repo.create(new_person.id)
    # Check if the person is already linked to the organization (via OrganizationPeople)
    org_person_exists = False

    return referral


@referral_router.get("/{referral_id}")
def get_referral(referral_id: int, repo: ReferralRepository = Depends(get_referral_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get(referral_id)


@referral_router.delete("/{referral_id}")
def soft_delete_referral(referral_id: int, repo: ReferralRepository = Depends(get_referral_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return {"success": repo.soft_delete(referral_id)}


@referral_router.get("/", response_model=ReferralResponseDTO)
def get_all_referrals(skip: int = Query(0, alias="page"), limit: int = Query(10),
                      searchtext: str = Query('', alias="searchtext"),
                      repo: ReferralRepository = Depends(get_referral_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get_all_referrals(skip=skip, limit=limit, search_text=searchtext)


@referral_router.put("/{referral_id}")
def update_referral(
        referral_id: int,
        referral: ReferralDTO,
        repo: ReferralRepository = Depends(get_referral_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    try:
        updated = repo.update_referral(referral_id, referral)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
    return updated
