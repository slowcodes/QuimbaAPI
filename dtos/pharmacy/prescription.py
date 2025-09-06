from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime

from dtos.consultation import ConsultantDTO
from dtos.people import ClientDTO
from dtos.pharmacy.drug import DrugDTO
from models.pharmacy import Form, PrescriptionStatus


class PrescriptionDetailDTO(BaseModel):
    id: Optional[int]
    drug: Optional[DrugDTO]
    dosage: Optional[str]
    frequency: Optional[int]
    duration: Optional[int]
    is_prn: Optional[bool]
    weight_volume: Optional[str]
    form: Optional[Form]
    status: Optional[PrescriptionStatus]
    interval: Optional[str]

    class Config:
        from_attributes=True


class PrescriptionDTO(BaseModel):
    id: Optional[int]
    status: Optional[PrescriptionStatus]
    prescriptions: Optional[list[PrescriptionDetailDTO]] = [];
    note: Optional[str]
    pharmacy_id: int
    client: Optional[ClientDTO] = None
    instruction: Optional[str]
    consultant: Optional[ConsultantDTO] = None
    created_at: Optional[str]

    class Config:
        from_attributes = True