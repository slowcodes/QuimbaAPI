from sqlalchemy.orm import Session
from typing import List, Optional

from dtos.client.allergy import FoodAllergyDTO, FoodAllergyUpdate, FoodAllergyCreate
from models.client import FoodAllergy


class FoodAllergyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, allergy_id: int) -> Optional[FoodAllergyDTO]:
        obj = self.db.query(FoodAllergy).filter(FoodAllergy.id == allergy_id).first()
        return FoodAllergyDTO.from_orm(obj) if obj else None

    def get_by_client(self, client_id: int) -> List[FoodAllergyDTO]:
        objs = self.db.query(FoodAllergy).filter(FoodAllergy.client_id == client_id).all()
        return [FoodAllergyDTO.from_orm(obj) for obj in objs]

    def create(self, payload: FoodAllergyCreate) -> FoodAllergyDTO:
        obj = FoodAllergy(**payload.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return FoodAllergyDTO.from_orm(obj)

    def update(self, db_obj: FoodAllergy, payload: FoodAllergyUpdate) -> FoodAllergyDTO:
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return FoodAllergyDTO.from_orm(db_obj)

    def delete(self, db_obj: FoodAllergy) -> None:
        self.db.delete(db_obj)
        self.db.commit()
