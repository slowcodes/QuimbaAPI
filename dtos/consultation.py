import datetime
from datetime import date, datetime as dtime

from pydantic import BaseModel, field_validator
from typing import Optional, List
from dtos.auth import BasicUserDTO
from dtos.services import BusinessServiceDTO
from models.consultation import InHourFrequency, ConsultationType, InternalSystems, CaseStatus


class SymptomDTO(BaseModel):
    id: Optional[int]
    symptom: str

    class Config:
        from_attributes = True


class PresentingSymptomDTO(BaseModel):
    clinical_examination_id: Optional[int] = None
    symptom_id: int
    severity: str
    frequency: str
    agreviating_factors: Optional[str] = None
    symptom: Optional[SymptomDTO] = None

    class Config:
        from_attributes = True


class SpecialismDTO(BaseModel):
    id: Optional[int]
    department: str
    specialist_title: str

    class Config:
        from_attributes = True


class ClinicalExaminationDTO(BaseModel):
    id: Optional[int] = None
    presenting_complaints: Optional[str] = ''
    conducted_at: Optional[date] = None
    conducted_by: Optional[int] = None  # only for response
    symptoms: List[PresentingSymptomDTO] = []
    transaction_id: int

    @field_validator("symptoms", mode="before")
    def convert_symptoms(cls, v):
        if v is None:
            return []
        # Convert SQLAlchemy models to DTOs if needed
        return [PresentingSymptomDTO.from_orm(item) if not isinstance(item, dict) else item for item in v]

    class Config:
        from_attributes = True


class InHoursDTO(BaseModel):
    id: Optional[int] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    specialist_id: Optional[int] = None
    frequency: Optional[InHourFrequency]

    business_service: Optional[BusinessServiceDTO]

    # consultant: Optional[ConsultantDTO] = None

    class Config:
        from_attributes = True


class SpecialistSpecializationDTO(BaseModel):
    id: Optional[int] = None
    specialist_id: int
    specialism_id: int

    specialism: Optional[SpecialismDTO] = None

    class Config:
        from_attributes = True


class ConsultantDTO(BaseModel):
    id: Optional[int] = None
    user_id: int
    title: Optional[str] = None
    user: BasicUserDTO

    specializations: List[SpecialistSpecializationDTO] = []
    in_hours: List[InHoursDTO] = []

    # consultant: List[ConsultationDTO] = None
    # prescriptions: List[PrescriptionDTO] = []
    # client_consultation_booking_carts: List[ClientConsultationBookingCartDTO] = []

    class Config:
        from_attributes = True
