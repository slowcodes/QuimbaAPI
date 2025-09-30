import datetime
from datetime import date, datetime as dtime

from pydantic import BaseModel, field_validator
from typing import Optional, List

from dtos.consultant import ConsultantDTO
from dtos.people import ClientDTO
from dtos.pharmacy.prescription import PrescriptionDTO
from dtos.service_dtos.client_cart_service import ClientServiceCartDTO
from dtos.services import BusinessServiceDTO
from models.consultation import QueueStatus, InHourFrequency, ConsultationType, InternalSystems, CaseStatus


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

    class Config:
        from_attributes = True


class ClinicalExaminationDTO(BaseModel):
    id: Optional[int] = None
    presenting_complaints: Optional[str] = ''
    conducted_at: Optional[date] = None
    conducted_by: Optional[int] = None  # only for response
    symptoms: List[PresentingSymptomDTO] =[]
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
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    specialist_id: Optional[int] = None
    frequency: Optional[InHourFrequency]
    business_service: Optional[BusinessServiceDTO]

    class Config:
        from_attributes = True


class BaseCaseDTO(BaseModel):
    consultation_id: int
    presenting_complaint: str
    preliminary_diagnosis: Optional[str] = None
    date_of_visit: dtime
    case_status: Optional[CaseStatus] = CaseStatus.Open


class ConsultationQueueDTO(BaseModel):
    id: Optional[int] = None
    schedule_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    status: Optional[QueueStatus] = QueueStatus.Processing
    booking_id: Optional[int] = None
    notes: Optional[str] = None
    booking_detail: Optional[dict] = None
    client: Optional[dict] = None
    specialization_id: Optional[int] = None
    consultation_time: Optional[str] = None
    base_cases: List[BaseCaseDTO] = []

    class Config:
        from_attributes = True


class ConsultationRoSDTO(BaseModel):
    id: Optional[int] = None
    system: Optional[InternalSystems]
    note: Optional[str] = ""
    consultation_id: Optional[int] = None

    class Config:
        from_attributes = True


class ConsultationAppointmentDTO(BaseModel):
    specialist: Optional[ConsultantDTO]
    client: Optional[ClientDTO]
    time_of_appointment: Optional[str] = None
    date_of_appointment: Optional[str] = None
    booking_id: Optional[int] = None
    transaction_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    status: Optional[str] = None
    id: Optional[int] = None


class ConsultationBase(BaseModel):
    consultation_type: ConsultationType = ConsultationType.base_case
    reason_for_visit: Optional[str] = None
    preliminary_diagnosis: Optional[str] = None
    base_case_id: Optional[int] = None
    # final_diagnosis: Optional[str] = None


class ConsultationCreate(ConsultationBase):
    queue_id: int


class ConsultationUpdate(ConsultationBase):
    pass


class ConsultationDTO(ConsultationBase):
    id: Optional[int] = None
    queue_id: int
    created_by: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    base_case_id: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True


class ConsultationRoSDTO(BaseModel):
    id: Optional[int] = None
    system: Optional[InternalSystems]
    note: Optional[str] = ""
    consultation_id: Optional[int] = None

    class Config:
        from_attributes = True


class ConsultationDetailDTO(BaseModel):
    consultation: ConsultationDTO
    clinical_examination: Optional[ClinicalExaminationDTO] = None
    review_of_systems: Optional[List[ConsultationRoSDTO]] = []
    client_service_cart: Optional[ClientServiceCartDTO] = None
    prescription: Optional[PrescriptionDTO] = None

    class Config:
        from_attributes = True
