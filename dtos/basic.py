from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.transaction import TransactionType


class BasicTransactionDTO(BaseModel):
    id: Optional[int] = None
    transaction_date: Optional[datetime] = None
    transaction_time: Optional[datetime] = None
    discount: float
    referral_id: Optional[int] = None
    transaction_status: Optional[TransactionType] = None

    class Config:
        from_attributes = True