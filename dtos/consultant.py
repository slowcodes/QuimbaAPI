import datetime
from datetime import date, datetime as dtime
from typing import Optional, List

from pydantic import BaseModel
from datetime import date

from dtos.auth import UserDTO, BasicUserDTO
from dtos.consultation import ConsultantDTO, ClinicalExaminationDTO
from dtos.people import ClientDTO
from dtos.service_dtos.client_cart_service import ClientServiceCartDTO
from dtos.services import ServiceBookingDetailDTO
from models.consultation import InternalSystems, CaseStatus, ConsultationType
from models.lab.lab import QueueStatus


class BaseCaseDTO(BaseModel):
    consultation_id: int
    presenting_complaint: str
    preliminary_diagnosis: Optional[str] = None
    date_of_visit: dtime
    case_status: Optional[CaseStatus] = CaseStatus.Open


class ConsultationQueueDTO(BaseModel):
    id: Optional[int] = None
    schedule_id: Optional[int] = None
    scheduled_at: Optional[date] = None
    status: Optional[QueueStatus] = QueueStatus.Processing
    booking_id: Optional[int] = None
    notes: Optional[str] = None
    booking_detail: Optional[ServiceBookingDetailDTO] = None
    client: Optional[dict] = None
    specialization_id: Optional[int] = None
    consultation_time: Optional[datetime.datetime] = None
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
    creator: Optional[ConsultantDTO] = None
    queue: Optional[ConsultationQueueDTO] = None
    case_status: Optional[CaseStatus] = CaseStatus.Open

    class Config:
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
    # prescription: Optional[PrescriptionDTO] = None

    class Config:
        from_attributes = True





