
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from enum import Enum

from dtos.auth import UserDTO
from dtos.people import ClientDTO
from dtos.services import BusinessServiceDTO
from models.consultation import QueueStatus, InHourFrequency


class ScheduleDTO(BaseModel):
    date_of_consultation: date
    specialist: int

    class Config:
        orm_mode = True
        from_attributes = True


class SpecialistDTO(BaseModel):
    user_id: int
    specialism: int

    class Config:
        orm_mode = True
        from_attributes = True


class ConsultationQueueDTO(BaseModel):
    schedule_id: int
    scheduled_at: Optional[date] = None
    status: Optional[QueueStatus] = QueueStatus.Processing
    booking_id: int

    class Config:
        orm_mode = True
        from_attributes = True


class SpecialismDTO(BaseModel):
    id: Optional[int]
    department: str
    specialist_title: str

    class Config:
        orm_mode = True
        from_attributes = True


class ConsultantDTO(BaseModel):
    id: Optional[int]
    user: UserDTO
    title: str
    specializations: List[SpecialismDTO] = []

    class Config:
        orm_mode = True
        from_attributes = True


class SymptomDTO(BaseModel):
    id: Optional[int]
    symptom: str

    class Config:
        orm_mode = True
        from_attributes = True


class PresentingSymptomDTO(BaseModel):
    clinical_examination_id: Optional[int] = None
    symptom_id: int
    severity: str
    frequency: str


class ClinicalExaminationDTO(BaseModel):
    id: Optional[int] = None
    presenting_complaints: str
    conducted_at: Optional[date] = None
    conducted_by: Optional[int] = None  # only for response
    symptoms: List[PresentingSymptomDTO]
    transaction_id: int


class InHoursDTO(BaseModel):
    id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    specialist_id: Optional[int] = None
    frequency: Optional[InHourFrequency]
    business_service: Optional[BusinessServiceDTO]

    class Config:
        orm_mode = True
        from_attributes = True


class ConsultationQueueDTO(BaseModel):
    id: Optional[int] = None
    schedule_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    status: Optional[QueueStatus] = QueueStatus.Processing
    booking_id: Optional[int] = None
    notes: Optional[str] = None
    specialization_id: Optional[int] = None
    consultation_time: Optional[str] = None


class ConsultationAppointmentDTO(BaseModel):
    specialist: Optional[ConsultantDTO]
    client: Optional[ClientDTO]
    time_of_appointment: Optional[str] = None
    date_of_appointment: Optional[str] = None
    booking_id: Optional[int] = None
    transaction_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    status:Optional[str] = None
    id: Optional[int] = None
