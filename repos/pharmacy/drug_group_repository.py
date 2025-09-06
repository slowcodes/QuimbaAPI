from sqlalchemy.orm import Session

from dtos.pharmacy.drug import DrugGroupDTO
from models.pharmacy import DrugGroup


class DrugGroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> DrugGroup | None:
        return self.db.query(DrugGroup).filter(DrugGroup.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(DrugGroup).offset(skip).limit(limit).all()

    def create(self, group_data: DrugGroupDTO) -> DrugGroup:
        new_group = DrugGroup(**group_data.dict())
        self.db.add(new_group)
        self.db.commit()
        self.db.refresh(new_group)
        return new_group

    def update(self, db_group: DrugGroup, updates: DrugGroupDTO) -> DrugGroup:
        for key, value in updates.dict(exclude_unset=True).items():
            setattr(db_group, key, value)
        self.db.commit()
        self.db.refresh(db_group)
        return db_group

    def delete(self, db_group: DrugGroup):
        # Soft delete assumed
        db_group.deleted = True
        self.db.commit()

    def get_by_parent_id(self, parent_id: int):
        return self.db.query(DrugGroup).filter(DrugGroup.parent_id == parent_id).all()
