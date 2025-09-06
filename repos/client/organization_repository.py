from sqlalchemy.orm import Session
from sqlalchemy import or_
import datetime
from typing import Optional, List

from dtos.people import OrganisationDTO, OrgType
from models.client import Organization, OrganizationPeople
from models.pharmacy import Pharmacy
from models.supply import Supplier
from repos.pharmacy.pharmacy_repository import PharmacyRepository


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db
        self.pharmacy_repo = PharmacyRepository(db)

    def is_org_exists(self, org_dto: OrganisationDTO) -> bool:
        return self.db.query(Organization).filter(
            (Organization.email == org_dto.email) | (Organization.phone == org_dto.name)
        ).count() > 0

    def create(self, org_dto: OrganisationDTO) -> Organization:
        """Create a new organization (and pharmacy if applicable)."""

        # Create the organization entity
        organization = Organization(
            name=org_dto.name,
            email=org_dto.email,
            phone=org_dto.phone,
            address=org_dto.address,
            lga_id=org_dto.lga_id,
        )

        # Save to database
        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)  # refresh before using the generated ID

        # Conditionally create pharmacy if it's a pharmacy
        if org_dto.org_type == 'Pharmacy':
            pharmacy = Pharmacy(is_active=True, org_id=organization.id)
            self.pharmacy_repo.add(pharmacy)

        if org_dto.org_type == 'Supplier':
            supplier = Supplier(org_id=organization.id)
            self.db.add(supplier)
            self.db.commit()

        return organization

    def get(self, org_id: int) -> Optional[Organization]:
        """Get an organization by ID (excluding soft deleted ones)."""
        return (
            self.db.query(Organization)
            .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
            .first()
        )

    def list(self, skip: int = 0, limit: int = 10) -> List[Organization]:
        """List all organizations with pagination (excluding soft deleted)."""
        return (
            self.db.query(Organization)
            .filter(Organization.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def soft_delete(self, org_id: int) -> bool:
        """Soft delete an organization."""
        organization = self.get(org_id)
        if not organization:
            return False

        organization.deleted_at = datetime.datetime.utcnow()
        self.db.commit()
        return True

    def restore(self, org_id: int) -> bool:
        """Restore a soft-deleted organization."""
        organization = (
            self.db.query(Organization)
            .filter(Organization.id == org_id, Organization.deleted_at.is_not(None))
            .first()
        )
        if not organization:
            return False

        organization.deleted_at = None
        self.db.commit()
        return True

    # def get_registered_orgs(self, limit, skip):
    #     all = self.session.query(Organization)
    #     return {
    #         'total': all.count(),
    #         'data': all.offset(skip).limit(limit).all()
    #     }

    def get_registered_orgs(self, limit: int, skip: int, org_type: OrgType = OrgType.Others):
        # Base columns
        cols = [
            Organization.id,
            Organization.name,
            Organization.email,
            Organization.phone,
            Organization.address
        ]

        # Start query
        query = self.db.query(*cols).select_from(Organization)

        if org_type == OrgType.Pharmacy:
            # Add Pharmacy column and perform a proper join
            cols.append(Pharmacy.id)
            query = self.db.query(*cols).select_from(Organization).join(
                Pharmacy, Pharmacy.org_id == Organization.id
            ).filter(Pharmacy.is_active.is_(True))

        if org_type == OrgType.Supplier:
            # Add Supplier specific logic if needed
            cols.append(Supplier.id)
            query = self.db.query(*cols).select_from(Organization).join(
                Supplier, Supplier.org_id == Organization.id
            )

        total = query.count()
        results = query.offset(skip).limit(limit).all()

        data = []
        for result in results:
            org_data = {
                "id": result[0],
                "name": result[1],
                "email": result[2],
                "phone": result[3],
                "address": result[4]
            }
            if org_type == OrgType.Pharmacy:
                org_data["pharmacy_id"] = result[5]
            elif org_type == OrgType.Supplier:
                org_data["supplier_id"] = result[5]
            data.append(org_data)

        return {
            "total": total,
            "data": data
        }

    def add_registered_org(self, org_dto: OrganisationDTO):
        org = Organization(**org_dto.__dict__)  # assuming `OrganisationDTO` has fields matching `Organization`
        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)
        return org

    def delete_registered_org(self, org_id: int):
        org = self.session.query(Organization).filter(Organization.id == org_id).one()
        if org:
            self.db.delete(org)
            self.db.commit()
            return True
        return False

    def update_registered_org(self, org_dto: OrganisationDTO):
        org = self.db.query(Organization).filter(Organization.id == org_dto.id).first()
        if org:
            data = org_dto.dict(exclude_unset=True)
            for key, value in data.items():
                setattr(org, key, value)
            self.db.commit()
            return True
        return False


class OrganizationPeopleRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_person_to_organization(self, person_id: int, org_id: int) -> OrganizationPeople:
        """Add a person to an organization."""
        membership = OrganizationPeople(person_id=person_id, organization_id=org_id)

        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def remove_person_from_organization(self, person_id: int, org_id: int) -> bool:
        """Remove a person from an organization."""
        membership = (
            self.db.query(OrganizationPeople)
            .filter(
                OrganizationPeople.person_id == person_id,
                OrganizationPeople.organization_id == org_id
            )
            .first()
        )

        if not membership:
            return False

        self.db.delete(membership)
        self.db.commit()
        return True

    def get_people_in_organization(self, org_id: int, skip: int = 0, limit: int = 10):
        """Get all people in an organization with pagination."""
        return (
            self.db.query(OrganizationPeople)
            .filter(OrganizationPeople.organization_id == org_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_person_and_org(self, person_id: int, organization_id: int | None) -> OrganizationPeople:
        """Retrieve the link between a person and an organization (if it exists)."""
        if not person_id or not organization_id:
            return False
        return self.db.query(OrganizationPeople).filter(
            OrganizationPeople.person_id == person_id,
            OrganizationPeople.organization_id == organization_id,
            OrganizationPeople.deleted_at == None  # Ensures the link isn't soft-deleted
        ).first()
