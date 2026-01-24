from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from dtos.admission.bed import BedDTO
from dtos.auth import BasicUserDTO

class AdmissionBaseDTO(BaseModel):
    bed_id: int
    patient_id: int
    admission_date: datetime
    reason: str
    user_id: int

    class Config:
        from_attributes = True


class AdmissionCreateDTO(AdmissionBaseDTO):
    pass


class AdmissionUpdateDTO(BaseModel):
    bed_id: Optional[int] = None
    patient_id: Optional[int] = None
    admission_date: Optional[datetime] = None
    reason: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class AdmissionDTO(AdmissionBaseDTO):
    id: Optional[int] = None
    bed: Optional[BedDTO] = None
    user: Optional[BasicUserDTO] = None
