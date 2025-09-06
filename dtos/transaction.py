from typing import Optional

from pydantic import BaseModel
from datetime import datetime, date

from models.transaction import PaymentMethod


class TransactionDTO(BaseModel):
    id: Optional[int] = None
    transaction_date: Optional[date] = None
    scheduled_at: Optional[datetime] = None  # Default is None if not provided
    discount: float
    referral_id: Optional[int] = None
    user_id: int  # should be jwt


class PaymentDTO(BaseModel):
    user_id: Optional[int] = None # Set at backend only
    payment_date: Optional[date] = None  # for response only
    payment_time: Optional[datetime] = None  # for response only
    amount: float
    transaction_id: Optional[int] = None
    payment_method: PaymentMethod


class ReferredTransactionDTO(BaseModel):
    id: Optional[int] = None
    transaction_id: int
    referral_id: int


class TransactionPackageDTO(BaseModel):
    id: Optional[int] = None
    transaction_id: int
    package_id: int

    class Config:
        from_attributes = True