from typing import Optional, List

from pydantic import BaseModel

from dtos.consultant import ConsultantDTO
from dtos.people import ClientDTO
from dtos.pharmacy.drug import DrugDTO
from models.pharmacy import Form, PrescriptionStatus


class PrescriptionDetailDTO(BaseModel):
    id: Optional[int] = None
    drug: Optional[DrugDTO] = None
    dosage: Optional[str]
    frequency: Optional[int]
    duration: Optional[int]
    is_prn: Optional[bool]
    weight_volume: Optional[str]
    form: Optional[Form]
    status: Optional[PrescriptionStatus] = None
    interval: Optional[str]

    class Config:
        from_attributes=True


class PrescriptionDTO(BaseModel):
    id: Optional[int] = None
    status: Optional[PrescriptionStatus] = None
    prescriptions: Optional[list[PrescriptionDetailDTO]] = [];
    note: Optional[str]
    pharmacy_id: int
    client: Optional[ClientDTO] = None
    instruction: Optional[str]
    consultant: Optional[ConsultantDTO] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True