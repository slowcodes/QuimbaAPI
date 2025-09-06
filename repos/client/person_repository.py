from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
import datetime

from dtos.people import PersonDTO
from models.client import Person


class PersonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, person_id: int) -> Optional[Person]:
        """Get a person by ID, excluding soft-deleted records."""
        return self.db.query(Person).filter(Person.id == person_id, Person.deleted_at.is_(None)).first()

    def list(self, skip: int = 0, limit: int = 10) -> List[Person]:
        """Retrieve active persons with pagination, excluding soft-deleted records."""
        return (
            self.db.query(Person)
            .filter(Person.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def person_exists(self, person_dto: PersonDTO) -> bool:
        # Build filter dynamically to handle cases where email or phone might be missing
        filters = []
        if person_dto.email:
            filters.append(Person.email == person_dto.email)
        if person_dto.phone:
            filters.append(Person.phone == person_dto.phone)

        if not filters:  # If neither email nor phone is provided, return False
            return False

        # Query database: Ensure we check both email & phone when both exist
        existing_person = (
            self.db.query(Person)
            .filter(and_(*filters))  # Ensures all non-null conditions are checked
            .one_or_none()
        )

        return existing_person is not None

    def create(self, person_dto: PersonDTO) -> Person:
        """Create a new person from a PersonDTO."""
        # Create a new Person model instance from the DTO data
        person = Person(
            first_name=person_dto.first_name,
            last_name=person_dto.last_name,
            middle_name=person_dto.middle_name,
            sex=person_dto.sex,
            email=person_dto.email,
            phone=person_dto.phone,
            enrollment_date=datetime.datetime.utcnow(),  # Automatically set the current time
        )

        # Add the person instance to the session and commit to the database
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)  # Refresh to get the ID and other fields after commit

        return person

    def soft_delete(self, person_id: int) -> bool:
        """Soft delete a person (mark as deleted)."""
        person = self.get(person_id)
        if not person:
            return False
        person.deleted_at = datetime.datetime.utcnow()  # Set soft delete timestamp
        self.db.commit()
        return True

    def restore(self, person_id: int) -> bool:
        """Restore a soft-deleted person by clearing deleted_at timestamp."""
        person = self.db.query(Person).filter(Person.id == person_id, Person.deleted_at.is_not(None)).first()
        if not person:
            return False
        person.deleted_at = None  # Remove the soft delete timestamp
        self.db.commit()
        return True

    def delete_permanently(self, person_id: int) -> bool:
        """Permanently delete a person (from the database)."""
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            return False
        self.db.delete(person)
        self.db.commit()
        return True

    def count(self) -> int:
        """Count the number of active (non-deleted) persons."""
        return self.db.query(Person).filter(Person.deleted_at.is_(None)).count()

    def count_all(self) -> int:
        """Count all persons (including soft-deleted)."""
        return self.db.query(Person).count()
