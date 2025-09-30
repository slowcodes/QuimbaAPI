from dataclasses import Field
from typing import Optional, List
from pydantic import BaseModel

from dtos.product import ProductDTO
from dtos.sales import SalesPriceCodeDTO
from models.pharmacy import Form


class DrugGroupDTO(BaseModel):
    id: Optional[int] = None
    group: Optional[str]
    use: Optional[str]
    parent_id: Optional[int]

    class Config:
        from_attributes = True


class PharmDrugPackageDTO(BaseModel):
    id: Optional[int] = None
    form_id: Optional[int] = None
    package_container: Optional[str] = None
    sales_price_code: Optional[SalesPriceCodeDTO] = None
    product_barcode: Optional[List[Optional[str]]] = None
    parent_package_id: Optional[int] = None
    quantity_per_parent: Optional[int] = None

    class Config:
        from_attributes=True

class DrugFormDTO(BaseModel):
    id: Optional[int] = None
    drug_id: Optional[int] = None
    drug_form: Optional[Form] = None
    form_packages: Optional[List[PharmDrugPackageDTO]]  = None

    class Config:
        from_attributes=True


class DrugInfoDTO(BaseModel):
    id: Optional[int] = None
    product_id: Optional[int] = None
    active_ingredients: Optional[str] = None
    storage_conditions: Optional[str] = None
    warnings: Optional[str] = None
    interactions: Optional[str] = None
    contraindications: Optional[str] = None
    side_effects: Optional[str] = None
    drug_form: Optional[List[DrugFormDTO]] = None
    drug_image_url: Optional[str] = None
    drug_group: Optional[List[DrugGroupDTO]] = None

    class Config:
        from_attributes=True


class DrugDTO(BaseModel):
    drug_info: Optional[DrugInfoDTO] = None
    product: Optional[ProductDTO] = None

    # No id needed for creation
    class Config:
        from_attributes=True
        use_enum_values = True  # To store enum values properly
