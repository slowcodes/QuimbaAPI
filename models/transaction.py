from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, Double, Integer, String, DateTime, Date, \
    Enum as SqlEnum, Text, \
    BLOB, Float, BIGINT, BigInteger
from sqlalchemy.orm import relationship
from models.mixins import SoftDeleteMixin

from db import Base
import datetime


class ServiceType(str, Enum):
    Laboratory = 'Laboratory'
    Consultation = 'Consultation'
    Dispensary = 'Dispensary'
    BloodBank = 'BloodBank'
    Admission = 'Admission'
    All = 'All'


class TransactionType(str, Enum):
    All = 'All'
    Open = 'Open'  # Incomplete payment
    Closed = 'Closed'  # Payment is complete


class Transaction(Base, SoftDeleteMixin):
    __tablename__ = "transaction"

    id = Column(BIGINT, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    transaction_date = Column(Date, default=datetime.date.today())
    transaction_time = Column(DateTime, default=datetime.datetime.utcnow)
    discount = Column(Float)  # float is recommended against double
    transaction_status = Column(SqlEnum(TransactionType), default=TransactionType.Open)

    # sales = relationship("BusinessSales", back_populates="transaction")
    client_service_carts = relationship("ClientServiceCart", back_populates="transaction")
    sales_services = relationship("ServiceBooking", back_populates="transaction", uselist=False,
                                  cascade="all, delete-orphan", passive_deletes=True)
    payment = relationship("Payments", back_populates="transaction")
    user = relationship("User", back_populates="transactions")
    referred_transaction = relationship("ReferredTransaction", back_populates="transaction", uselist=False)
    package_transactions = relationship("PackageTransaction", back_populates="transaction",  uselist=True)

class PaymentMethod(str, Enum):
    PoS = 'PoS'
    BankTransfer = 'BankTransfer'
    Paystack = 'Paystack'
    Cash = 'Cash'


class ReferredTransactionStatus(str, Enum):
    Settled = 'Settled'
    UnSettled = 'UnSettled'


class Payments(Base, SoftDeleteMixin):
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="cascade"))
    payment_date = Column(Date, default=datetime.date.today())
    payment_time = Column(DateTime, default=datetime.datetime.utcnow)
    amount = Column(Float)
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))
    payment_method = Column(SqlEnum(PaymentMethod), default=PaymentMethod.Cash)

    transaction = relationship("Transaction", back_populates="payment")
    user = relationship("User")


class PackageTransaction(Base, SoftDeleteMixin):
    __tablename__ = "package_transaction"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("service_bundle.id", ondelete="cascade"))
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))

    transaction = relationship("Transaction", back_populates="package_transactions")
    package = relationship("Bundles", back_populates="package_transactions")


class ReferredTransaction(Base, SoftDeleteMixin):
    __tablename__ = "referred_transaction"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))
    referral_id = Column(Integer, ForeignKey("client_referral.id", ondelete="cascade"
                                             ))  # A client may have been referred multiple times by different refferals
    status = Column(SqlEnum(ReferredTransactionStatus), default=ReferredTransactionStatus.UnSettled)
    transaction = relationship("Transaction", back_populates="referred_transaction")
    referral = relationship("Referral", back_populates="referred_transactions")


class ReferredTransactionSettlement(Base, SoftDeleteMixin):
    __tablename__ = "referred_transaction_settlement"
    id = Column(Integer, primary_key=True, index=True)
    created_for = Column(Integer, ForeignKey("client_referral.id", ondelete="cascade"
                                             ))  # A client may have been referred multiple times by different refferals
    commission = Column(Float)
    created_at = Column(Date, default=datetime.date.today())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))

    user = relationship("User")
    referral = relationship("Referral")
    settlement_detail = relationship("ReferredTransactionSettlementDetail", back_populates="settlement", uselist=True)


class ReferredTransactionSettlementDetail(Base, SoftDeleteMixin):
    __tablename__ = "referred_transaction_settlement_detail"
    id = Column(BigInteger, primary_key=True, index=True)
    settlement_id = Column(Integer, ForeignKey("referred_transaction_settlement.id", ondelete="cascade"))
    ref_transaction_id = Column(BigInteger, ForeignKey("transaction.id", ondelete="cascade")) # transaction_id is also unique

    settlement = relationship("ReferredTransactionSettlement", back_populates="settlement_detail", uselist=False)
    transaction = relationship("Transaction")