from enum import Enum
from typing import Optional, List

from pydantic import BaseModel

from commands.lab import LabBundleCollectionDTO
from models.services import ServiceType


class ServiceBookingDetailDTO(BaseModel):
    id: Optional[int] = None
    service_id: int
    price_code: int
    booking_id: Optional[int]


class ServiceBookingDTO(BaseModel):
    id: Optional[int]
    client_id: int
    transaction_id: int
    booking_type: Optional[str]
    booking_status: Optional[str]
    transaction_time: Optional[str]
    client_first_name: Optional[str]
    client_last_name: Optional[str]


class ServiceBundleDTO(BaseModel):
    id: Optional[int]
    bundles_name: Optional[str]
    bundles_desc: Optional[str]
    discount: float
    bundle_type: ServiceType

    class Config:
        orm_mode = True


class LabServiceBundleDTO(ServiceBundleDTO):
    collections: List[LabBundleCollectionDTO]

    class Config:
        orm_mode = False


class EventType(str, Enum):
    Booking = 'Booking'
    Queuing = 'Queuing'
    SampleCollection = 'Sample'
    Result = 'Result'
    Verification = 'Verification'
    Issuance = 'Issuance'


class ServiceEventDTO(BaseModel):
    event_time: str
    event_type: EventType
    event_desc: str

    class Config:
        orm_mode = False


class ServiceTrackingDTO(BaseModel):
    queue_id: int
    booked_service: str
    service_tracking_details: List[ServiceEventDTO]
    complete: float

    class Config:
        orm_mode = False


class TrackingDataDTO(BaseModel):
    service_tracking: List[ServiceEventDTO]
    transaction: dict

    class Config:
        orm_mode = False
