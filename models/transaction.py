from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, Double, Integer, String, DateTime, Date, \
    Enum as SqlEnum, Text, \
    BLOB, Float, BIGINT
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

    sales = relationship("BusinessSales", back_populates="transaction")

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


class PackageTransaction(Base, SoftDeleteMixin):
    __tablename__ = "package_transaction"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("service_bundle.id", ondelete="cascade"))
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))


class ReferredTransaction(Base, SoftDeleteMixin):
    __tablename__ = "referred_transaction"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))
    referral_id = Column(Integer, ForeignKey("client_referral.id", ondelete="cascade"
                                         ))  # A client may have been referred multiple times by different refferals
    status = Column(SqlEnum(ReferredTransactionStatus), default=ReferredTransactionStatus.UnSettled)


class ReferredTransactionSettlement(Base, SoftDeleteMixin):
    __tablename__ = "referred_transaction_settlement"
    id = Column(Integer, primary_key=True, index=True)
    created_for = Column(Integer, ForeignKey("client_referral.id", ondelete="cascade"
                                         ))  # A client may have been referred multiple times by different refferals
    created_at = Column(Date, default=datetime.date.today())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))


class ReferredTransactionSettlementDetail(Base, SoftDeleteMixin):
    __tablename__ = "referred_transaction_settlement_detail"
    id = Column(Integer, primary_key=True, index=True)
    settlement_id = Column(Integer, ForeignKey("referred_transaction_settlement.id", ondelete="cascade"))
    ref_transaction_id = Column(Integer, ForeignKey("referred_transaction.id", ondelete="cascade"))