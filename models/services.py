from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from db import Base
from enum import Enum
from models.consultation import ClinicalExaminations
from models import transaction


class BusinessServices(Base):
    __tablename__ = "Service_Listing"

    id = Column(Integer, primary_key=True, index=True)
    price_code = Column(String(30))
    ext_turn_around_time = Column(Double)


class Bundles(Base):
    __tablename__ = "Service_Bundle"

    id = Column(Integer, primary_key=True, index=True)
    bundles_name = Column(String(100))
    bundles_desc = Column(String(100))


class BundleCollection(Base):
    __tablename__ = "Service_Bundle_Collection"

    id = Column(Integer, primary_key=True, index=True)
    bundles_id = Column(Integer, ForeignKey("Service_Bundle.id", ondelete='CASCADE'))
    service_id = Column(Integer, ForeignKey("Service_Listing.id", ondelete='CASCADE'))
    discount = Column(Double)


class ServiceBooking(Base):
    __tablename__ = "Service_Booking"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("Service_Listing.id", ondelete='CASCADE'))
    price_code = Column(Integer, ForeignKey("Service_Price_Code.id", ondelete='CASCADE'))
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    transaction_id = Column(Integer, ForeignKey("Transaction.id", ondelete='CASCADE'))


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
