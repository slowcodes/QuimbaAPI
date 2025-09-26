from sqlalchemy.orm import Session
from typing import List, Optional

from dtos.client.allergy import DrugAllergyDTO, DrugAllergyCreate, DrugAllergyUpdate
from models.client import DrugAllergy
from models.pharmacy import Drug
from models.product import Product


class DrugAllergyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, allergy_id: int) -> Optional[DrugAllergyDTO]:
        obj = self.db.query(DrugAllergy).filter(DrugAllergy.id == allergy_id).first()
        return DrugAllergyDTO.from_orm(obj) if obj else None

    def get_by_client(self, client_id: int) -> List[DrugAllergyDTO]:
        cols = [DrugAllergy, Product.product_name.label('drug')]
        objs = self.db.query(*cols).join(Drug, DrugAllergy.drug_id == Drug.id) \
            .join(Product, Product.id == Drug.product_id) \
            .filter(DrugAllergy.client_id == client_id).all()

        result = []
        for obj, drug_name in objs:  # unpack the tuple
            dto = DrugAllergyDTO.from_orm(obj)
            dto.drug_name = drug_name  # set the extra field
            result.append(dto)
        return result

    def create(self, payload: DrugAllergyCreate) -> DrugAllergyDTO:
        obj = DrugAllergy(**payload.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return DrugAllergyDTO.from_orm(obj)

    def update(self, db_obj: DrugAllergy, payload: DrugAllergyUpdate) -> DrugAllergyDTO:
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return DrugAllergyDTO.from_orm(db_obj)

    def delete(self, db_obj: DrugAllergy) -> None:
        self.db.delete(db_obj)
        self.db.commit()
