from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from dtos.auth import BasicUserDTO
from dtos.basic import BasicTransactionDTO
from dtos.people import ClientDTO, BasicClientDTO, ReferralDTO
from models.services.services import ServiceType, StoreVisibility


class ServiceBookingLightDTO(BaseModel):
    id: int
    client_id: int
    transaction_id: int
    booking_status: Optional[str] = None


class CopyApprovedLabBookingResultDTO(BaseModel):
    id: Optional[int] = None
    booking_id: int
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    comment: Optional[str] = None
    status: str

    user: Optional[BasicUserDTO] = None

    class Config:
        from_attributes = True


class ServiceBookingWithTrxDTO(BaseModel):
    id: Optional[int] = None
    client_id: int
    transaction_id: int
    booking_status: Optional[str] = None

    client: Optional[BasicClientDTO] = None
    transaction: Optional[BasicTransactionDTO] = None

    class Config:
        from_attributes = True

class ServiceBookingDTO(BaseModel):
    id: Optional[int] = None
    client_id: int
    transaction_id: int
    referral_id: Optional[int] = None
    client: Optional[BasicClientDTO] = None
    lab_booking_completion: int = 0
    booking_status: Optional[str] = None
    result_approval: Optional[CopyApprovedLabBookingResultDTO] = None  # Placeholder for ApprovedLabBookingResultDTO

    class Config:
        from_attributes = True


class ServiceBookingDetailDTO(BaseModel):
    id: Optional[int] = None
    service_id: int
    price_code: int
    booking_id: Optional[int] = None
    booking_type: Optional[str] = None

    booking: Optional[ServiceBookingDTO] = None  # forward ref as string
    price_code_rel: Optional['PriceCodeDTO'] = None
    business_service: Optional['BusinessServiceDTO'] = None

    model_config = ConfigDict(from_attributes=True)


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
    price_code: Optional[int] = None
    pc: Optional[PriceCodeDTO] = None
    ext_turn_around_time: float
    visibility: Optional[StoreVisibility]
    service_type: Optional[ServiceType]

    class Config:
        from_attributes = True
