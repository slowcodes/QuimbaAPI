from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from dtos.lab import LabBundleCollectionDTO
from dtos.people import ClientDTO
from models.services.services import ServiceType, StoreVisibility


class ServiceBookingDetailDTO(BaseModel):
    id: Optional[int] = None
    service_id: int
    price_code: int
    booking_id: Optional[int] = None
    booking_type: Optional[str] = None


class ServiceBookingDTO(BaseModel):
    id: Optional[int] = None
    client_id: int
    transaction_id: int
    client: Optional[ClientDTO] = None
    booking_status: Optional[str] = None
    transaction_time: Optional[str] = None
    client_first_name: Optional[str] = None
    client_last_name: Optional[str] = None


class ServiceBundleDTO(BaseModel):
    id: Optional[int] = None
    bundles_name: Optional[str] = None
    bundles_desc: Optional[str] = None
    discount: float
    bundle_type: ServiceType

    class Config:
        # orm_mode = True
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
        from_attributes = True


class ServiceTrackingDTO(BaseModel):
    queue_id: int
    booked_service: str
    service_tracking_details: List[ServiceEventDTO]
    complete: float

    class Config:
        from_attributes = True


class TrackingDataDTO(BaseModel):
    service_tracking: List[ServiceEventDTO]
    transaction: dict

    class Config:
        from_attributes = True


class PriceCodeDTO(BaseModel):
    id: Optional[int] = None
    service_price: float
    discount: float

    class Config:
        from_attributes = True


class BusinessServiceDTO(BaseModel):
    service_id: Optional[int] = None
    price_code: Optional[PriceCodeDTO]
    ext_turn_around_time: float
    visibility: Optional[StoreVisibility]
    serviceType: Optional[ServiceType]
