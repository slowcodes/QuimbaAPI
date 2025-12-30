import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, \
    BLOB, BIGINT

from db import Base
from enum import Enum
from sqlalchemy.orm import relationship

from models.mixins import SoftDeleteMixin


class StoreVisibility(str, Enum):
    Disabled = 'Disabled'
    Active = 'Active'


class ServiceType(str, Enum):
    Laboratory = 'Laboratory'
    # Pharmacy = 'Pharmacy'
    Administration = 'Administration'  # e.g enrollment
    Consultation = 'Consultation'
    Appointment = 'Appointment'
    Enrollment = 'Enrollment'


class BusinessServices(Base):
    __tablename__ = "service_listing"

    service_id = Column(Integer, primary_key=True, index=True)
    price_code = Column(Integer, ForeignKey("service_price_code.id", ))
    ext_turn_around_time = Column(Double)
    visibility = Column(SqlEnum(StoreVisibility))
    service_type = Column("service_type", SqlEnum(ServiceType), nullable=False)

    # relationships
    in_hours = relationship("InHours", back_populates="business_service")
    pc = relationship("PriceCode", back_populates="business_services")
    lab_service = relationship("LabService", back_populates="business_service", lazy="joined", uselist=False)
    booking_detail = relationship("ServiceBookingDetail", back_populates="business_service")


class BundleStatus(str, Enum):
    Active = 'Active'
    Suspended = 'Suspended'


class Bundles(Base, SoftDeleteMixin):
    __tablename__ = "service_bundle"

    id = Column(Integer, primary_key=True, index=True)
    bundles_name = Column(String(100))
    bundles_desc = Column(String(100))
    discount = Column(Double)
    bundle_type = Column(SqlEnum(BundleStatus), default=BundleStatus.Active)

    lab_service_bundle = relationship("LabBundleCollection", back_populates="bundle", uselist=True)
    package_transactions = relationship("PackageTransaction", back_populates="package")


class BookingStatus(str, Enum):
    Processing = 'Processing'
    Processed = 'Processed'
    Suspended = 'Suspended'
    Verified = 'All Verified'


class BookingType(str, Enum):
    Laboratory = 'Laboratory'
    Consultation = 'Consultation'
    Appointment = 'Appointment'
    Dispensary = 'Dispensary'
    Aggregate = 'Aggregate'
    Enrollment = 'Enrollment'


class ServiceBooking(Base):
    __tablename__ = "service_booking"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"), nullable=False, unique=True)
    booking_status = Column(SqlEnum(BookingStatus), default=BookingStatus.Processing)
    referral_id = Column(Integer, ForeignKey("client_referral.id", ondelete="cascade"), nullable=True)

    booking_detail = relationship("ServiceBookingDetail", back_populates="booking", uselist=True)
    client = relationship("Client", back_populates="service_bookings")
    # referral = relationship("Referral", back_populates="service_bookings")
    business_sales = relationship("BusinessSales", back_populates="sales_service")
    transaction = relationship("Transaction", back_populates="sales_services")
    result_approval = relationship("ApprovedLabBookingResult", back_populates="booking", uselist=False)


class ServiceBookingDetail(Base):
    __tablename__ = "service_booking_detail"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("service_listing.service_id", ondelete="cascade"))
    price_code = Column(Integer, ForeignKey("service_price_code.id", ondelete="cascade"))
    booking_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade"))
    booking_type = Column(SqlEnum(BookingType), default=BookingType.Laboratory)

    consultation_queue = relationship("ConsultationQueue", back_populates="booking_detail", uselist=False)
    booking = relationship("ServiceBooking", back_populates="booking_detail")
    business_service = relationship("BusinessServices", back_populates="booking_detail")
    price_code_rel = relationship("PriceCode", back_populates="service_booking_detail", uselist=False)
    lab_service_queue = relationship("LabServicesQueue", back_populates="booking", uselist=False)


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

    business_services = relationship("BusinessServices", back_populates="pc")
    service_booking_detail = relationship("ServiceBookingDetail", back_populates="price_code_rel")


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
