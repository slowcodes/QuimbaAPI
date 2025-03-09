from typing import List, Optional

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from commands.people import ClientCommand, UserDTO
from models.lab.lab import BoundaryType, QueueStatus, QueuePriority, SampleType, ExperimentResultReading, ResultStatus
from models.services import StoreVisibility


class LaboratoryDTO(BaseModel):
    lab: str
    description: str


class LaboratoryGroupDTO(BaseModel):
    group_name: str
    group_desc: str


class CommandParameterBoundary(BaseModel):
    upper_bound: str
    lower_bound: str
    boundary_type: BoundaryType
    key: Decimal


class CommandParameter(BaseModel):
    name: str
    unit: str
    paramKey: Decimal
    type: str
    boundary: List[CommandParameterBoundary]


class CommandExperiment(BaseModel):
    name: str
    key: str
    parameter: List[CommandParameter]


class CommandLaboratoryService(BaseModel):
    groups: List[int]
    name: str
    description: str
    exps: List[CommandExperiment]
    price: Decimal
    discount: Decimal
    visibility: StoreVisibility
    lab_id: int
    est_turn_around_time: int


class LabServicesQueueDTO(BaseModel):
    id: Optional[int]
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


class QueueDTO(BaseModel):
    total: int
    total_processed: int
    queue: List[QueueListingDTO]


class CollectedSamplesDTO(BaseModel):
    id: Optional[int]
    queue_id: int
    sample_type: SampleType
    collected_by: int
    container_label: str
    collected_at: Optional[datetime]


class ExperimentResultReadingDTO(BaseModel):
    id: Optional[int]
    parameter_id: int
    parameter_value: str
    sample_id: int
    created_at: Optional[datetime]


class SampleResultDTO(BaseModel):
    id: Optional[int]
    created_at: Optional[datetime]
    sample_id: int
    created_by: int
    comment: str
    experiment_readings: Optional[List[ExperimentResultReadingDTO]]


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
    client: ClientCommand;


class VerifiedResultEntryDTO(BaseModel):
    id: Optional[int]
    result_id: int
    verified_at: Optional[datetime]
    verified_by: Optional[int]
    comment: Optional[str]
    status: Optional[str]


class DateFilterDTO(BaseModel):
    start_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    status: Optional[QueueStatus]


class LabBundleCollectionDTO(BaseModel):
    id: Optional[int]
    bundles_id: Optional[int]
    lab_service_id: Optional[int]
    lab_service_name: Optional[str]

    class Config:
        orm_mode = True


class ApprovedLabBookingResultDTO(BaseModel):
    id: Optional[int]
    booking_id: int
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    comment: Optional[str]
    status: str
    approved_user: Optional[UserDTO]

    class Config:
        orm_mode = True


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
