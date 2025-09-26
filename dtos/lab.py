from typing import List, Optional

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from dtos.auth import UserDTO
from dtos.people import ClientDTO
from models.lab.lab import BoundaryType, QueueStatus, QueuePriority, SampleType, ResultStatus
from models.services.services import StoreVisibility


class LaboratoryDTO(BaseModel):
    id: Optional[int] = None
    lab: str
    description: str


class LaboratoryGroupDTO(BaseModel):
    group_name: str
    group_desc: str


class ParameterBoundaryDTO(BaseModel):
    upper_bound: str
    lower_bound: str
    boundary_type: BoundaryType
    boundary_id: Optional[Decimal] = None


class ParameterDTO(BaseModel):
    name: str
    unit: str
    paramKey: Decimal
    type: str
    boundary: List[ParameterBoundaryDTO]


class ExperimentDTO(BaseModel):
    name: str
    key: str
    parameter: List[ParameterDTO]


class LabServiceDTO(BaseModel):
    id: Optional[int] = None
    lab_id: Optional[int] = None
    lab_service_name: Optional[str] = None
    lab_service_desc: Optional[str] = None
    service_id: Optional[int] = None


class LaboratoryServiceDetailDTO(BaseModel):
    lab_service_id: Optional[int] = None
    groups: List[int]
    name: str
    description: str
    exps: List[ExperimentDTO]
    price: Decimal
    discount: Decimal
    visibility: StoreVisibility
    lab_id: int
    est_turn_around_time: int


class LabServicesQueueDTO(BaseModel):
    id: Optional[int] = None
    lab_service_id: int
    scheduled_at: Optional[datetime] = None  # Default is None if not provided
    status: Optional[QueueStatus] = QueueStatus.Processing  # Default is None if not provided
    priority: Optional[QueuePriority] = QueuePriority.Normal
    booking_id: int


class QueueListingDTO(BaseModel):
    id: int
    scheduled_at: datetime
    lab_service: str
    laboratory: str
    status: QueueStatus
    priority: QueuePriority
    est_delivery_time: int
    client_first_name: str
    client_last_name: str
    booking_ref: int


class QueueDTO(BaseModel):
    total: int
    total_processed: int
    queue: List[QueueListingDTO]


class CollectedSamplesDTO(BaseModel):
    id: Optional[int] = None
    queue_id: int
    sample_type: SampleType
    collected_by: int
    container_label: str
    collected_at: Optional[datetime] = None


class ExperimentResultReadingDTO(BaseModel):
    id: Optional[int] = None
    parameter_id: int
    parameter_value: str
    sample_id: int
    created_at: Optional[datetime] = None


class SampleResultDTO(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    sample_id: int
    created_by: int
    comment: str
    experiment_readings: Optional[List[ExperimentResultReadingDTO]]=None


class ServiceAgent(BaseModel):
    first_name: str
    last_name: str


class Queue(BaseModel):
    queue_status: str
    queue_priority: str
    queue_id: int
    queue_booking_time: str


class SampleDetailDTO(BaseModel):
    sample_type: SampleType
    sample_id: int
    collected_at: str
    lab_service_id: int
    container_label: str
    service_agent: ServiceAgent
    lab_service_name: str
    queue: Queue
    client: ClientDTO;


class VerifiedResultEntryDTO(BaseModel):
    id: Optional[int] = None
    result_id: int
    verified_at: Optional[datetime] = None
    verified_by: Optional[UserDTO] = None
    comment: Optional[str] = None
    status: Optional[str] = None


class DateFilterDTO(BaseModel):
    start_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    status: Optional[QueueStatus]


class LabBundleCollectionDTO(BaseModel):
    id: Optional[int] = None
    bundles_id: Optional[int] = None
    lab_service_id: Optional[int] = None
    lab_service_name: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


class ApprovedLabBookingResultDTO(BaseModel):
    id: Optional[int] = None
    booking_id: int
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    comment: Optional[str] = None
    status: str
    approved_user: Optional[UserDTO] = None

    class Config:
        orm_mode = True
        from_attributes = True


class LabResultLogBase(BaseModel):
    booking_id: int
    logged_by: int
    action: ResultStatus


class LabResultLogCreate(LabResultLogBase):
    pass  # No extra fields required when creating a new log


class LabResultLogUpdate(BaseModel):
    action: Optional[ResultStatus]  # Only allow updating the action field


class LabResultLogResponse(LabResultLogBase):
    id: int
    logged_at: datetime

    class Config:
        orm_mode = True  # Enables ORM compatibility with SQLAlchemy
        from_attributes = True