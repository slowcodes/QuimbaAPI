from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from dtos.people import ReferralDTO, ReferralResponseDTO
from dtos.transaction import ReferredTransactionDTO
from models.client import Referral, OrganizationPeople, Person
from models.transaction import ReferredTransaction


class ReferralRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, org_people_id: Optional[int]) -> Referral:
        """Create a new referral."""
        referral = Referral(org_people_id=org_people_id)
        self.db.add(referral)
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def get_referral_by_id(self, referral_id: int) -> Optional[Referral]:
        """Retrieve a referral by ID."""
        return self.db.query(Referral).filter(Referral.id == referral_id, Referral.deleted_at.is_(None)).first()

    def list(self) -> List[Referral]:
        """Get all active (non-deleted) referrals with joined Person and Organization."""
        return (
            self.db.query(Referral)
            .options(joinedload(Referral.person), joinedload(Referral.organization))
            .filter(Referral.deleted_at.is_(None))
            .all()
        )

    def update(self, referral_id: int, person_id: Optional[int] = None, organization_id: Optional[int] = None) -> \
            Optional[Referral]:
        """Update an existing referral."""
        referral = self.get(referral_id)
        if not referral:
            return None
        if person_id is not None:
            referral.person_id = person_id
        if organization_id is not None:
            referral.organization_id = organization_id
        referral.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def soft_delete(self, referral_id: int) -> bool:
        """Soft delete a referral (mark as deleted)."""
        referral = self.get(referral_id)
        if not referral:
            return False
        referral.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def delete_permanently(self, referral_id: int) -> bool:
        """Permanently delete a referral from the database."""
        referral = self.db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            return False
        self.db.delete(referral)
        self.db.commit()
        return True

    def get_all_referrals(self, skip: int = 0, limit: int = 10, search_text: str = '') -> ReferralResponseDTO:
        """Retrieve all referrals with joined Person and Organization data, with pagination."""

        query = self.db.query(Referral)
        if search_text:
            query = query.join(Person, Person.id == Referral.person_id).filter(Person.first_name.ilike(f'%{search_text}%') | Person.last_name.ilike(f'%{search_text}%') | Person.middle_name.ilike(f'%{search_text}%') | Person.phone.ilike(f'%{search_text}%'))

        query = query.all()
        counter = len(query)
        query = query[skip: skip + limit]

        return ReferralResponseDTO(
            data=[ReferralDTO.from_orm(ref) for ref in query],
            total=counter
        )

    def get_active_referrals(self, skip: int = 0, limit: int = 10) -> List[Referral]:
        """Retrieve only active (non-deleted) referrals with pagination."""
        return (
            self.db.query(Referral)
            .options(joinedload(Referral.organization))
            .filter(Referral.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, transaction_id: int):
        return self.db.query(ReferredTransaction).filter(ReferredTransaction.id == transaction_id).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(ReferredTransaction).offset(skip).limit(limit).all()

    def create_referred_transaction(self, transaction_data: ReferredTransactionDTO):
        db_transaction = ReferredTransaction(**transaction_data.dict())
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def get_referred_transaction_referral(self, transaction_id: int):
        cols = [
            ReferredTransaction.transaction_id,
            Referral.id,
            Person.first_name,
            Person.last_name,
            Person.middle_name,
            ReferredTransaction.status
        ]
        rs = self.db.query(*cols).select_from(OrganizationPeople)\
            .join(Referral, Referral.org_people_id == OrganizationPeople.id) \
            .join(Person, Person.id == OrganizationPeople.person_id) \
            .join(ReferredTransaction, ReferredTransaction.referral_id == Referral.id) \
            .filter(ReferredTransaction.transaction_id == transaction_id).first()
        if rs:
            return {
                'first_name': rs.first_name,
                'last_name': rs.last_name,
                'middle_name': rs.middle_name,
                'referral_id': rs.id,
                'status': rs.status
            }
        return None

    def get_referred_transaction(self, transaction_id: int):
        return self.db.query(ReferredTransaction).filter(ReferredTransaction.id == transaction_id).first()

    def get_all_referred_transaction(self, skip: int = 0, limit: int = 100):
        return self.db.query(ReferredTransaction).offset(skip).limit(limit).all()

    def create_referred_transaction(self, transaction_data: ReferredTransactionDTO):
        db_transaction = ReferredTransaction(**transaction_data.dict())
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction
