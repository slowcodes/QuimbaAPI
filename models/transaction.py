from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, Double, Integer, String, DateTime, Date, \
    Enum as SqlEnum, Text, \
    BLOB, Float
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
    Open = 'Open' # Incomplete payment
    Closed = 'Closed' # Payment is complete


class Transaction(Base):
    __tablename__ = "Transaction"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    transaction_date = Column(Date, default=datetime.date.today())
    transaction_time = Column(DateTime, default=datetime.datetime.utcnow)
    discount = Column(Float)  # float is recommended against double
    transaction_status = Column(SqlEnum(TransactionType), default=TransactionType.Open)

class PaymentMethod(str, Enum):
    PoS = 'PoS'
    BankTransfer = 'BankTransfer'
    Paystack = 'Paystack'
    Cash = 'Cash'


class Payments(Base):
    __tablename__ = "Payment"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    payment_date = Column(Date, default=datetime.date.today())
    payment_time = Column(DateTime, default=datetime.datetime.utcnow)
    amount = Column(Float)
    transaction_id = Column(Integer, ForeignKey("Transaction.id", ondelete='CASCADE'))
    payment_method = Column(SqlEnum(PaymentMethod), default=PaymentMethod.Cash)
