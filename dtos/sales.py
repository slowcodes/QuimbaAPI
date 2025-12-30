from typing import Optional

from pydantic import BaseModel
from datetime import datetime, date

from models.product import PackagingType


class SalesPriceCodeDTO(BaseModel):
    id: Optional[int] = None
    selling_price: Optional[float] = None
    buying_price: Optional[float] = None

    class Config:
        from_attributes = True


class BusinessSalesBase(BaseModel):
    id: Optional[int] = None
    package_id: Optional[int] = None
    transaction_id: Optional[int] = None
    sale_service_id: Optional[int] = None
    per_package_sales_code_id: Optional[int] = None
    quantity: Optional[int] = None
    product_id: Optional[int] = None


# --- Create DTO ---
class BusinessSalesCreate(BusinessSalesBase):
    pass

    # --- Read DTO ---


class TransactionCopyDTO(BaseModel):
    id: Optional[int] = None
    transaction_date: Optional[date] = None
    scheduled_at: Optional[datetime] = None  # Default is None if not provided
    discount: float
    referral_id: Optional[int] = None
    user_id: int

    class Config:
        from_attributes = True


class PharmDrugPackageCopyDTO(BaseModel):
    id: Optional[int] = None
    form_id: Optional[int] = None
    package_container: Optional[PackagingType] = None
    sales_price_code_id: Optional[int] = None

    sales_price_code: Optional[SalesPriceCodeDTO] = None

    class Config:
        from_attributes = True


class ProductCopyDTO(BaseModel):
    id: Optional[int] = None
    manufacturer: Optional[str] = None
    brand_name: Optional[str] = None
    product_name: str
    product_desc: Optional[str] = None

    class Config:
        from_attributes = True


class BusinessSalesRead(BusinessSalesBase):
    id: int
    transaction: Optional[TransactionCopyDTO] = None
    package: Optional[PharmDrugPackageCopyDTO] = None
    product: Optional[ProductCopyDTO] = None

    class Config:
        from_attributes = True
