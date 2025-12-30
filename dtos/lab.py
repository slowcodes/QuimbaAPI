from typing import List, Optional, Union

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from dtos.auth import UserDTO, BasicUserDTO
from dtos.people import ClientDTO
from dtos.services import ServiceBookingDetailDTO, BusinessServiceDTO, PriceCodeDTO
from models.lab.lab import BoundaryType, QueueStatus, QueuePriority, SampleType, ResultStatus, ParameterType, LabType
from models.services.services import StoreVisibility, ServiceType


class LaboratoryDTO(BaseModel):
    id: Optional[int] = None
    lab_name: str
    lab_desc: str = None

    class Config:
        from_attributes = True


class LaboratoryGroupDTO(BaseModel):
    group_name: str
    group_desc: str

    class Config:
        from_attributes = True


class LabServiceGroupTagDTO(BaseModel):
    id: Optional[int] = None
    lab_service_group: int
    lab_service_id: int
    group: Optional[LaboratoryGroupDTO] = None

    class Config:
        from_attributes = True


class ParameterBoundaryDTO(BaseModel):
    upper_bound: str
    lower_bound: str
    boundary_type: BoundaryType
    boundary_id: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ExperimentParameterDTO(BaseModel):
    id: Union[int, float, str] = None
    parameter: str
    measuring_unit: str
    parameter_type: ParameterType
    exp_id: Optional[int] = None
    boundary: List[ParameterBoundaryDTO] = []

    class Config:
        from_attributes = True


class ExpDTO(BaseModel):
    id: Optional[int] = None
    description: str = None
    parameters: List[ExperimentParameterDTO] = []

    class Config:
        from_attributes = True


class LabServiceExperimentDTO(BaseModel):
    id: Optional[int] = None
    lab_service_id: int
    experiment_id: int

    experiment: Optional[ExpDTO]

    class Config:
        from_attributes = True


class LabServiceDTO(BaseModel):
    id: Optional[int] = None
    lab_id: Optional[int] = None
    lab_service_name: Optional[str] = None
    lab_service_desc: Optional[str] = None
    service_id: Optional[int] = None
    lab_type: LabType

    business_service: Optional[BusinessServiceDTO] = None
    lab_experiments: List[LabServiceExperimentDTO] = []
    laboratory: Optional[LaboratoryDTO] = None
    lab_service_group_tag: List[LabServiceGroupTagDTO] = []

    class Config:
        from_attributes = True


class LaboratoryServiceDetailDTO(BaseModel):
    lab_service_id: Optional[int] = None
    groups: List[int]
    name: str
    description: str
    exps: List[ExpDTO]
    lab_type: LabType
    price: Decimal
    discount: Decimal
    visibility: StoreVisibility
    lab_id: int
    est_turn_around_time: int


class LabServicesQueueCreateDTO(BaseModel):
    lab_service_id: int
    booking_id: int


class LabServiceQueueBase(BaseModel):
    id: Optional[int] = None
    lab_service_id: int
    scheduled_at: Optional[datetime] = None  # Default is None if not provided
    status: Optional[QueueStatus] = QueueStatus.Processing  # Default is None if not provided
    priority: Optional[QueuePriority] = QueuePriority.Normal
    booking_id: int

    booking: Optional[ServiceBookingDetailDTO] = []
    lab_service: Optional[LabServiceDTO] = None

    class Config:
        from_attributes = True

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


class CollectedSamplesBaseDTO(BaseModel):
    id: Optional[int] = None
    queue_id: int
    sample_type: SampleType
    collected_by: int
    status: Optional[QueueStatus] = QueueStatus.Processing
    container_label: str


class CollectedSamplesCreateDTO(BaseModel):
    id: Optional[int] = None
    queue_id: int
    sample_type: SampleType
    collected_by: int
    status: Optional[QueueStatus] = QueueStatus.Processing
    container_label: str

    class Config:
        from_attributes = True


class ExperimentResultReadingDTO(BaseModel):
    id: Optional[int] = None
    parameter_id: int
    parameter_value: str
    result_id: int
    created_at: Optional[datetime] = None

    parameter: Optional[ExperimentParameterDTO] = None

    class Config:
        from_attributes = True


class VerifiedResultEntryDTO(BaseModel):
    id: Optional[int] = None
    result_id: int
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    comment: Optional[str] = None
    status: Optional[str] = None

    user: Optional[BasicUserDTO] = None

    class Config:
        from_attributes = True


class SampleResultDTO(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    queue_id: int
    created_by: int
    comment: str
    status: Optional[ResultStatus] = ResultStatus.Ready

    experiment_readings: Optional[List[ExperimentResultReadingDTO]] = None
    user: Optional[BasicUserDTO] = None
    verification: Optional[VerifiedResultEntryDTO] = None
    queue: Optional[LabServiceQueueBase] = None

    class Config:
        from_attributes = True


class LabServicesQueueDTO(LabServiceQueueBase):
    lab_result: Optional[SampleResultDTO] = None

    class Config:
        from_attributes = True


class CollectedSamplesDTO(CollectedSamplesBaseDTO):
    user: Optional[BasicUserDTO] = None
    queue: Optional[LabServicesQueueDTO] = None

    collected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LabResultByQueueDTO(LabServiceQueueBase):
    sample: Optional[CollectedSamplesDTO] = None
    lab_result: Optional[SampleResultDTO] = None


    class Config:
        from_attributes = True


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
    service_agent: Optional[BasicUserDTO] = None
    lab_service_name: str
    queue: Queue
    client: ClientDTO;


class DateFilterDTO(BaseModel):
    start_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    status: Optional[str]


class LabBusinessServiceDTO(BaseModel):
    service_id: Optional[int] = None
    price_code: Optional[int] = None
    pc: Optional[PriceCodeDTO] = None
    ext_turn_around_time: float
    visibility: Optional[StoreVisibility]
    service_type: Optional[ServiceType]

    lab_service: Optional[LabServiceDTO] = None

    class Config:
        from_attributes = True


class LabBundleCollectionDTO(BaseModel):
    id: Optional[int] = None
    bundles_id: Optional[int] = None
    lab_service_id: Optional[int] = None

    lab_service: Optional[LabServiceDTO] = None

    class Config:
        from_attributes = True


class LabServiceBundleDTO(BaseModel):
    id: Optional[int] = None
    bundles_name: Optional[str] = None
    bundles_desc: Optional[str] = None
    discount: float
    bundle_type: ServiceType
    collections: List[LabBundleCollectionDTO]

    class Config:
        from_attributes = True


class ApprovedLabBookingResultDTO(BaseModel):
    id: Optional[int] = None
    booking_id: int
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    comment: Optional[str] = None
    status: str

    user: Optional[BasicUserDTO] = None

    class Config:
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
