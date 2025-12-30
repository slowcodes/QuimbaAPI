from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from dtos.consultation import ConsultantDTO
from dtos.people import ClientDTO, BasicClientDTO
from dtos.pharmacy.drug import DrugDTO
from models.pharmacy import Form, PrescriptionStatus
from dtos.client.organization import OrganisationDTO


class PharmacyDTO(BaseModel):
    id: Optional[int] = None
    is_active: Optional[bool] = None
    org_id: Optional[int] = None

    company: Optional[OrganisationDTO] = None

    class Config:
        from_attributes = True


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
        from_attributes = True


class PrescriptionDTO(BaseModel):
    id: Optional[int] = None
    status: Optional[PrescriptionStatus] = None
    prescriptions: Optional[list[PrescriptionDetailDTO]] = [];
    note: Optional[str]
    pharmacy_id: int
    client_id: Optional[int]
    instruction: Optional[str]
    created_at: Optional[datetime] = None

    client: Optional[BasicClientDTO] = None
    consultant: Optional[ConsultantDTO] = None
    pharmacy: Optional[PharmacyDTO] = None
    prescriptions: List[PrescriptionDetailDTO] = []

    class Config:
        from_attributes = True
