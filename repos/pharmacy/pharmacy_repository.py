from models.client import Organization
from models.pharmacy import Pharmacy
from repos.base_repository import BaseRepository


class PharmacyRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)

    def get_pharmacy_by_id(self, pharmacy_id: int):
        return (
            self.db.query(Organization).join(Pharmacy, Pharmacy.org_id == Organization.id)
            .filter(Pharmacy.id == pharmacy_id, Organization.deleted_at.is_(None))
            .first()
        )