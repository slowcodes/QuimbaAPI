from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime, date

from dtos.auth import BasicUserDTO
from dtos.people import ReferralDTO, BasicReferralDTO
from dtos.service_dtos.bundles import BundleDTO
from dtos.services import ServiceBookingDTO
from models.transaction import PaymentMethod, TransactionType


class PaymentDTO(BaseModel):
    user_id: Optional[int] = None  # Set at backend only
    payment_date: Optional[date] = None  # for response only
    payment_time: Optional[datetime] = None  # for response only
    amount: float
    transaction_id: Optional[int] = None
    payment_method: PaymentMethod
    id: Optional[int] = None

    user: Optional[BasicUserDTO] = None

    class Config:
        from_attributes = True


class TransactionCreateDTO(BaseModel):
    discount: float
    referral_id: Optional[int] = None
    user_id: int


class ReferredTransactionDTO(BaseModel):
    id: Optional[int] = None
    transaction_id: int
    referral_id: int
    status: Optional[str] = None

    referral: Optional[ReferralDTO] = None

    class Config:
        from_attributes = True


class TransactionBaseDTO(BaseModel):
    id: Optional[int] = None
    transaction_date: Optional[datetime] = None
    transaction_time: Optional[datetime] = None
    discount: float
    referral_id: Optional[int] = None
    transaction_status: Optional[TransactionType] = None
    user_id: int


class TransactionPackageDTO(BaseModel):
    id: Optional[int] = None
    transaction_id: int
    package_id: int

    package: Optional[BundleDTO] = None

    class Config:
        from_attributes = True


class TransactionDTO(TransactionBaseDTO):
    pass

    user: BasicUserDTO
    payment: Optional[list[PaymentDTO]] = []
    sales_services: Optional[ServiceBookingDTO] = None
    referred_transaction: Optional[ReferredTransactionDTO] = None
    package_transactions: list[TransactionPackageDTO] = []

    class Config:
        from_attributes = True


# ---------- REFERRED TRANSACTION DTOs ----------

class ReferredTransactionSettlementDetailCreateDTO(BaseModel):
    ref_transaction_id: int


class ReferredTransactionSettlementCreateDTO(BaseModel):
    created_for: int
    commission: float
    created_by: Optional[int] = None
    transactions: List[int]


# ---------- RESPONSE DTOs ----------

class ReferredTransactionSettlementDetailResponseDTO(BaseModel):
    id: int
    ref_transaction_id: int
    transaction: TransactionDTO

    class Config:
        from_attributes = True


class ReferredTransactionSettlementResponseDTO(BaseModel):
    id: int
    created_for: int
    commission: float
    created_at: date
    created_by: Optional[int] = None
    settlement_detail: List[ReferredTransactionSettlementDetailResponseDTO] = []

    user: BasicUserDTO
    referral: BasicReferralDTO

    class Config:
        from_attributes = True
