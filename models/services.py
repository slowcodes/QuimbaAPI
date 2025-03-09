import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from sqlalchemy.orm import relationship

from db import Base
from enum import Enum
from models.consultation import ClinicalExamination
from models import transaction


class StoreVisibility(str, Enum):
    Disabled = 'Disabled'
    Active = 'Active'


class ServiceType(str, Enum):
    Laboratory = 'Laboratory'
    Pharmacy = 'Pharmacy'
    Administration = 'Administration'  # e.g enrollment
    Consultation = 'Consultation'


class BusinessServices(Base):
    __tablename__ = "Service_Listing"

    service_id = Column(Integer, primary_key=True, index=True)
    price_code = Column(Integer, ForeignKey("Service_Price_Code.id", ondelete='CASCADE'))
    ext_turn_around_time = Column(Double)
    visibility = Column(SqlEnum(StoreVisibility))
    serviceType = Column(SqlEnum(ServiceType))


class Bundles(Base):
    __tablename__ = "Service_Bundle"

    id = Column(Integer, primary_key=True, index=True)
    bundles_name = Column(String(100))
    bundles_desc = Column(String(100))
    discount = Column(Double)
    bundle_type = Column(SqlEnum(ServiceType))


class BookingStatus(str, Enum):
    Processing = 'Processing'
    Processed = 'Processed'
    Suspended = 'Suspended'
    Verified = 'All Verified'


class BookingType(str, Enum):
    Laboratory = 'Laboratory'
    Consultation = 'Consultation'


class ServiceBooking(Base):
    __tablename__ = "Service_Booking"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    transaction_id = Column(Integer, ForeignKey("Transaction.id", ondelete='CASCADE'))
    booking_status = Column(SqlEnum(BookingStatus), default=BookingStatus.Processing)
    booking_type = Column(SqlEnum(BookingType), default=BookingType.Laboratory)


class ServiceBookingDetail(Base):
    __tablename__ = "Service_Booking_Detail"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("Service_Listing.service_id", ondelete='CASCADE'))
    price_code = Column(Integer, ForeignKey("Service_Price_Code.id", ondelete='CASCADE'))
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))


class ServiceClinicalExamination(Base):
    __tablename__ = "Service_Booking_Clinical_Examination"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))
    clinical_examination_id = Column(Integer, ForeignKey("Clinical_Examination.id", ondelete='CASCADE'))


class PriceCode(Base):
    __tablename__ = "Service_Price_Code"

    id = Column(Integer, primary_key=True, index=True)
    service_price = Column(Double)
    discount = Column(Double)


class CommunicationMode(str, Enum):
    Email = 'Email'
    SMS = 'SMS'
    WhatsApp = 'WhatsApp'
    Phone = 'Phone'


class BookingCommunication(Base):
    __tablename__ = "Service_Booking_Communication"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))
    mode = Column(SqlEnum(CommunicationMode))


class BookingCommunicationLog(Base):
    __tablename__ = "Service_Booking_Communication_Log"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))
    mode = Column(SqlEnum(CommunicationMode))
    message = Column(String(100))
    status = Column(String(100))
    log_time = Column(DateTime, default=datetime.datetime.utcnow)
