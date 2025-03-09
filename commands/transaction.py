from typing import Optional

from pydantic import BaseModel
from datetime import datetime, date

from models.transaction import PaymentMethod


class TransactionDTO(BaseModel):
    id: Optional[int]
    transaction_date: Optional[date]
    scheduled_at: Optional[datetime] = None  # Default is None if not provided
    discount: float
    user_id: int  # should be jwt


class PaymentDTO(BaseModel):
    user_id: Optional[int]  # Set at backend only
    payment_date: Optional[date]  # for response only
    payment_time: Optional[date]  # for response only
    amount: float
    transaction_id: int
    payment_method: PaymentMethod