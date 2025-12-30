from typing import Optional, List
# import datetime
from datetime import date, datetime as dtime
from pydantic import BaseModel

from dtos.auth import BasicUserDTO
from dtos.consultation import ConsultantDTO
from dtos.people import BasicClientDTO, BasicReferralDTO
from dtos.pharmacy.prescription import PrescriptionDTO, PrescriptionDetailDTO
from dtos.services import BusinessServiceDTO, PriceCodeDTO
from models.consultation import InHourFrequency
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

    # client_service_cart: Optional[ClientServiceCartDTO] = None

    def to_orm_model(self):
        return ClientConsultationBookingCart(
            id=self.id,
            cart_detail_id=self.cart_detail_id,
            consultant_id=self.consultant_id,
            specialization_id=self.specialization_id,
            schedule_id=self.schedule_id,
            note=self.note,
            scheduled_time=self.scheduled_time,
            # client_service_cart=
        )


class InHoursDTO2(BaseModel):
    id: Optional[int] = None
    start_time: Optional[dtime] = None
    end_time: Optional[dtime] = None
    specialist_id: Optional[int] = None
    frequency: Optional[InHourFrequency]

    business_service: Optional[BusinessServiceDTO]
    consultant: Optional[ConsultantDTO] = None

    class Config:
        from_attributes = True


class ClientConsultationBookingCartDTO(BaseModel):
    id: Optional[int] = None
    cart_detail_id: Optional[int] = None
    consultant_id: Optional[int] = None
    specialization_id: int
    schedule_id: int
    note: str
    scheduled_time: dtime

    consultant: Optional[ConsultantDTO] = None
    schedule: Optional[InHoursDTO2] = None

    # specialization: Optional[SpecialismDTO] = None

    class Config:
        from_attributes = True


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
    service_desc: Optional[str] = None

    price_code: Optional[PriceCodeDTO] = None
    client_consultation_booking_carts: List[ClientConsultationBookingCartDTO] = []

    class Config:
        from_attributes = True


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


class ConsultationPrescriptionDTO(BaseModel):
    id: Optional[int] = None
    consultation_cart_id: Optional[int] = None
    prescription_id: Optional[int] = None
    pharmacy_id: Optional[int] = None
    instruction: Optional[str] = None
    note: Optional[str] = None

    pharmacy_prescription: Optional[PrescriptionDTO] = None
    client: Optional[BasicClientDTO] = None
    consultant: Optional[ConsultantDTO] = None
    prescriptions: List[PrescriptionDetailDTO] = []

    class Config:
        from_attributes = True


class ClientServiceCartDTO(ClientServiceCartBase):
    id: Optional[int] = None
    created_at: Optional[dtime] = None
    created_by: Optional[int] = None

    client: Optional[BasicClientDTO] = None
    user: Optional[BasicUserDTO] = None

    # nested relations
    client_service_cart_packages: List[ClientServiceCartPackageDTO] = []
    client_service_cart_details: List[ClientServiceCartDetailDTO] = []
    client_referral: Optional[BasicReferralDTO] = None
    prescription: Optional[ConsultationPrescriptionDTO] = None

    class Config:
        from_attributes = True


class ProcessedCartDTO(BaseModel):
    cart_id: int
    client_id: int
    processed_services: List[int] = []
