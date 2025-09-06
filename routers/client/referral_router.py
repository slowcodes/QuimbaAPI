from http.client import HTTPException

from fastapi import APIRouter, Depends, Query

from dtos.people import ReferralDTO, PersonDTO, OrganisationDTO
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
                    org_people_repo: OrganizationPeopleRepository = Depends(get_organization_people_repository),
                    org_repo: OrganizationRepository = Depends(get_organization_repository)):
    """Creates a referral by checking if person and organization exist."""

    # Check if person already exists by email or phone
    person_exists = people_repo.person_exists(referral.person)

    # Check if organization exists by email or phone

    # If either person or organization exists, raise an error
    if person_exists:
        raise HTTPException(400, "Person or organization exist")

    # Create person if they don't exist
    new_person = people_repo.create(referral.person)

    # Check if the person is already linked to the organization (via OrganizationPeople)
    org_person_exists = False
    if referral.org.id:
        org_person_exists = org_people_repo.get_by_person_and_org(new_person.id, referral.org.id)

    # If the link doesn't exist, create a new org_people entry
    if not org_person_exists:
        org_people = org_people_repo.add_person_to_organization(new_person.id, referral.org.id)
    else:
        org_people = org_person_exists  # Use the existing link if it exists

    # Now org_people is always defined, so we can safely pass it to Referral.create
    referral = repo.create(org_people.id)

    return referral


@referral_router.get("/{referral_id}")
def get_referral(referral_id: int, repo: ReferralRepository = Depends(get_referral_repository)):
    return repo.get(referral_id)


@referral_router.delete("/{referral_id}")
def soft_delete_referral(referral_id: int, repo: ReferralRepository = Depends(get_referral_repository)):
    return {"success": repo.soft_delete(referral_id)}


@referral_router.get("/")
def get_all_referrals(skip: int = Query(0, alias="page"), limit: int = Query(10),
                      repo: ReferralRepository = Depends(get_referral_repository)):
    return repo.get_all_referrals(skip=skip, limit=limit)
