from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from models.services.service_cart import ClientConsultationBookingCart
from models.services.services import BookingType, BookingStatus


class AppointmentData(BaseModel):
    id: Optional[int] = None
    cart_detail_id: Optional[int] = None
    consultant_id: Optional[int] = None
    specialization_id: int
    schedule_id: int
    note: str
    scheduled_time: str

    def to_orm_model(self):
        return ClientConsultationBookingCart(
            id=self.id,
            cart_detail_id=self.cart_detail_id,
            consultant_id=self.consultant_id,
            specialization_id=self.specialization_id,
            schedule_id=self.schedule_id,
            note=self.note,
            scheduled_time=self.scheduled_time,
        )


class ClientServiceCartDetailBase(BaseModel):
    price_code_id: int
    service_id: int
    service_type: BookingType = BookingType.Laboratory
    appointment_data: Optional[AppointmentData] = None


class ClientServiceCartDetailCreate(ClientServiceCartDetailBase):
    pass


class ClientServiceCartDetailDTO(ClientServiceCartDetailBase):
    id: Optional[int] = None
    cart_id: Optional[int] = None

    class Config:
        orm_mode = True


class ClientServiceCartPackageBase(BaseModel):
    package_id: int


class ClientServiceCartPackageCreate(ClientServiceCartPackageBase):
    pass


class ClientServiceCartPackageDTO(ClientServiceCartPackageBase):
    id: int
    cart_id: int

    class Config:
        orm_mode = True


class ClientServiceCartBase(BaseModel):
    client_id: int
    cart_status: BookingStatus = BookingStatus.Processing
    referral_id: Optional[int] = None
    transaction_id: Optional[int] = None


class ClientServiceCartCreate(ClientServiceCartBase):
    created_by: int


class ClientServiceCartDTO(ClientServiceCartBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

    # nested relations
    client_service_cart_packages: List[ClientServiceCartPackageDTO] = []
    client_service_cart_details: List[ClientServiceCartDetailDTO] = []

    class Config:
        orm_mode = True
