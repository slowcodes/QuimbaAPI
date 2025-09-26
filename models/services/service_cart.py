import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SqlEnum, BIGINT, Text
from sqlalchemy.orm import relationship
from db import Base
from models.consultation import SoftDeleteMixin
from models.services.services import BookingStatus, BookingType


class ClientServiceCart(Base):
    __tablename__ = "client_service_cart"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    cart_status = Column(SqlEnum(BookingStatus), default=BookingStatus.Processing)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    referral_id = Column(Integer, ForeignKey("client_referral.id", ondelete="SET NULL"), nullable=True)
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="SET NULL"), nullable=True)

    # relationships
    client = relationship("Client", back_populates="service_carts")
    user = relationship("User", back_populates="client_service_cart")
    client_referral = relationship("Referral", back_populates="client_service_carts")
    transaction = relationship("Transaction", back_populates="client_service_carts")

    client_service_cart_packages = relationship(
        "ClientServiceCartPackage",
        back_populates="client_service_cart",
        cascade="all, delete-orphan"
    )
    client_service_cart_details = relationship(
        "ClientServiceCartDetail",
        back_populates="client_service_cart",
        cascade="all, delete-orphan"
    )


class ClientServiceCartPackage(Base, SoftDeleteMixin):
    __tablename__ = "client_service_cart_package"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("service_bundle.id", ondelete="cascade"))
    cart_id = Column(BIGINT, ForeignKey("client_service_cart.id", ondelete="cascade"))

    service_bundle = relationship("Bundles", backref="client_service_cart_packages")
    client_service_cart = relationship("ClientServiceCart", back_populates="client_service_cart_packages")


class ClientServiceCartDetail(Base):
    __tablename__ = "client_service_cart_detail"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("client_service_cart.id", ondelete="cascade"))
    price_code_id = Column(Integer, ForeignKey("service_price_code.id", ondelete="cascade"))
    service_id = Column(Integer, ForeignKey("service_listing.service_id", ondelete="cascade"))
    service_type = Column(SqlEnum(BookingType), default=BookingType.Laboratory)
    processing_status = Column(SqlEnum(BookingStatus), default=BookingStatus.Processing, nullable=False)

    # relationships
    client_service_cart = relationship("ClientServiceCart", back_populates="client_service_cart_details")
    price_code = relationship("PriceCode", backref="client_service_cart_details")
    service = relationship("BusinessServices", backref="client_service_cart_details")


class ClientConsultationBookingCart(Base):
    __tablename__ = "client_consultation_booking_cart"

    id = Column(Integer, primary_key=True, index=True)
    cart_detail_id = Column(Integer, ForeignKey("client_service_cart_detail.id", ondelete="cascade"))
    consultant_id = Column(Integer, ForeignKey("consultant_specialist.id", ondelete="cascade"))
    specialization_id = Column(Integer, ForeignKey("consultant_specialist_specialization.id"))
    schedule_id = Column(Integer, ForeignKey("consultant_in_hours.id"))
    note = Column(Text)
    scheduled_time = Column(DateTime)
