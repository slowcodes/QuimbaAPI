import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, \
    BLOB, BIGINT

from db import Base
from enum import Enum
from sqlalchemy.orm import relationship

from models.consultation import SoftDeleteMixin


class StoreVisibility(str, Enum):
    Disabled = 'Disabled'
    Active = 'Active'


class ServiceType(str, Enum):
    Laboratory = 'Laboratory'
    # Pharmacy = 'Pharmacy'
    Administration = 'Administration'  # e.g enrollment
    Consultation = 'Consultation'
    Appointment = 'Appointment'


class BusinessServices(Base):
    __tablename__ = "service_listing"

    service_id = Column(Integer, primary_key=True, index=True)
    price_code = Column(Integer, ForeignKey("service_price_code.id", ))
    ext_turn_around_time = Column(Double)
    visibility = Column(SqlEnum(StoreVisibility))
    serviceType = Column(SqlEnum(ServiceType))


class Bundles(Base):
    __tablename__ = "service_bundle"

    id = Column(Integer, primary_key=True, index=True)
    bundles_name = Column(String(100))
    bundles_desc = Column(String(100))
    discount = Column(Double)
    bundle_type = Column(SqlEnum(ServiceType))

    lab_service_bundle = relationship("LabBundleCollection", back_populates="bundle")


class BookingStatus(str, Enum):
    Processing = 'Processing'
    Processed = 'Processed'
    Suspended = 'Suspended'
    Verified = 'All Verified'


class BookingType(str, Enum):
    Laboratory = 'Laboratory'
    Consultation = 'Consultation'
    Appointment = 'Appointment'


class ServiceBooking(Base):
    __tablename__ = "service_booking"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))
    booking_status = Column(SqlEnum(BookingStatus), default=BookingStatus.Processing)
    # booking_type = Column(SqlEnum(BookingType), default=BookingType.Laboratory)


class ServiceBookingDetail(Base):
    __tablename__ = "service_booking_detail"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("service_listing.service_id", ondelete="cascade"))
    price_code = Column(Integer, ForeignKey("service_price_code.id", ondelete="cascade"))
    booking_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade"))
    booking_type = Column(SqlEnum(BookingType), default=BookingType.Laboratory)


class ServiceClinicalExamination(Base):
    __tablename__ = "service_booking_clinical_examination"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ))
    clinical_examination_id = Column(Integer, ForeignKey("clinical_examination.id", ))


class PriceCode(Base):
    __tablename__ = "service_price_code"

    id = Column(Integer, primary_key=True, index=True)
    service_price = Column(Double)
    discount = Column(Double)


class CommunicationMode(str, Enum):
    Email = 'Email'
    SMS = 'SMS'
    WhatsApp = 'WhatsApp'
    Phone = 'Phone'


class BookingCommunication(Base):
    __tablename__ = "service_booking_communication"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ))
    mode = Column(SqlEnum(CommunicationMode))


class BookingCommunicationLog(Base):
    __tablename__ = "service_booking_communication_log"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("service_booking.id", ))
    mode = Column(SqlEnum(CommunicationMode))
    message = Column(String(100))
    status = Column(String(100))
    log_time = Column(DateTime, default=datetime.datetime.utcnow)
