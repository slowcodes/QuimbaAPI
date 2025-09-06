from sqlalchemy.orm.query import Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from dtos.people import VitalDTO
from models.client import Vitals


class VitalsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_vital(self, vital_dto: VitalDTO) -> Vitals:
        """
        Creates a new Vital record using the VitalDTO.
        """
        new_vital = Vitals(
            vital_type=vital_dto.vital_type,
            vital_value=vital_dto.vital_value,
            client_id=vital_dto.client_id,
        )
        self.db.add(new_vital)
        self.db.commit()
        self.db.refresh(new_vital)
        return new_vital

    def get_vital_by_id(self, vital_id: int) -> Optional[Vitals]:
        """
        Retrieves a single Vital record by ID.
        """
        return self.db.query(Vitals).filter(Vitals.id == vital_id).first()

    def get_vitals_by_client_id(self, client_id: int, skip: int = 0, limit: int = 10, vital_type: str = None) -> List[Vitals]:
        """
        Retrieves paginated Vital records for a given client.

        :param client_id: The ID of the client whose vitals are to be retrieved.
        :param skip: The number of records to skip.
        :param limit: The maximum number of records to retrieve.
        :return: A list of Vital records.
        """
        query = self.db.query(Vitals).filter(Vitals.client_id == client_id)
        if vital_type:
            query = query.filter(Vitals.vital_type == vital_type)

        return {
            'data': query.offset(skip).limit(limit).all(),
            'total': self.vital_count(vital_type)
        }

    def vital_count(self, vital_type: str = None):
        if vital_type:
            return self.db.query(Vitals).filter(Vitals.vital_type == vital_type).count()
        return self.db.query(Vitals).count()

    def update_vital(self, vital_id: int, vital_dto: VitalDTO) -> Optional[Vitals]:
        """
        Updates an existing Vital record using the VitalDTO.
        """
        vital = self.get_vital_by_id(vital_id)
        if not vital:
            return None
        vital.vital_type = vital_dto.vital_type
        vital.vital_value = vital_dto.vital_value
        vital.client_id = vital_dto.client_id
        vital.created_at = datetime.utcnow()  # Update the timestamp
        self.db.commit()
        self.db.refresh(vital)
        return vital

    def delete_vital(self, vital_id: int) -> bool:
        """
        Deletes a Vital record by ID.
        """
        vital = self.get_vital_by_id(vital_id)
        if not vital:
            return False
        self.db.delete(vital)
        self.db.commit()
        return True
