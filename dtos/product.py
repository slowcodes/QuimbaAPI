from typing import Optional, List
from pydantic import BaseModel, Field
from dtos.sales import SalesPriceCodeDTO


class ProductPackageDTO(BaseModel):
    id: Optional[int] = None
    product_id: Optional[int] = None
    package_container: Optional[str] = None
    sales_price_code_id: Optional[int] = None
    sales_price_code: Optional[SalesPriceCodeDTO] = None
    product_barcode: Optional[List[Optional[str]]] = Field(default_factory=list)
    parent_package_id: Optional[int] = None
    quantity_per_parent: Optional[int] = None

    class Config:
        from_attributes=True


class ProductDTO(BaseModel):
    id: Optional[int] = None
    manufacturer: Optional[str] = None
    brand_name: Optional[str] = None
    product_name: str
    product_desc: Optional[str] = None
    product_package: Optional[List[ProductPackageDTO]] = None

    class Config:
        from_attributes=True
