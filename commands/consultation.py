from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from enum import Enum

from models.consultation import QueueStatus


class ScheduleDTO(BaseModel):
    date_of_consultation: date
    specialist: int


class SpecialistDTO(BaseModel):
    user_id: int
    specialism: int


class ConsultationQueueDTO(BaseModel):
    schedule_id: int
    scheduled_at: Optional[date] = None
    status: Optional[QueueStatus] = QueueStatus.Processing
    booking_id: int


class SymptomDTO(BaseModel):
    id: Optional[int]
    symptom: str


class PresentingSymptomDTO(BaseModel):
    clinical_examination_id: Optional[int]
    symptom_id: int
    severity: str
    frequency: str


class ClinicalExaminationDTO(BaseModel):
    id: Optional[int]
    presenting_complaints: str
    conducted_at: Optional[date]
    conducted_by: Optional[int]  # only for response
    symptoms: List[PresentingSymptomDTO]
    transaction_id: int
