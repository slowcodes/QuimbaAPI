from pydantic import BaseModel
from typing import Optional

from dtos.pharmacy.drug import DrugDTO
from models.client import Severity


# -----------------------------
# DrugAllergy DTOs
# -----------------------------

class DrugAllergyBase(BaseModel):
    detail: Optional[str] = None
    risk_severity: Optional[Severity] = None


class DrugAllergyCreate(DrugAllergyBase):
    drug_id: int
    client_id: int


class DrugAllergyUpdate(DrugAllergyBase):
    drug_id: Optional[int] = None
    client_id: Optional[int] = None


class DrugAllergyDTO(DrugAllergyBase):
    id: int
    drug_id: int
    client_id: int
    drug_name: Optional[str] = None  # To avoid circular import issues, we use str instead of DrugDTO

    class Config:
        from_attributes = True


# -----------------------------
# FoodAllergy DTOs
# -----------------------------

class FoodAllergyBase(BaseModel):
    food: str
    detail: Optional[str] = None
    risk_severity: Optional[Severity] = None


class FoodAllergyCreate(FoodAllergyBase):
    client_id: int


class FoodAllergyUpdate(FoodAllergyBase):
    food: Optional[str] = None
    client_id: Optional[int] = None


class FoodAllergyDTO(FoodAllergyBase):
    id: int
    client_id: int

    class Config:
        from_attributes = True
