from dataclasses import Field
from typing import Optional, List
from pydantic import BaseModel, field_serializer

from dtos.product import ProductDTO
from dtos.sales import SalesPriceCodeDTO
from models.pharmacy import Form
from models.product import PackagingType


class DrugGroupDTO(BaseModel):
    id: Optional[int] = None
    group: Optional[str]
    use: Optional[str]
    parent_id: Optional[int]

    class Config:
        from_attributes = True


class DrugGroupTagDTO(BaseModel):
    id: Optional[int] = None
    drug_id: Optional[int] = None
    group_id: Optional[int] = None

    group: Optional[DrugGroupDTO] = None

    class Config:
        from_attributes = True


class PharmDrugPackageDTO(BaseModel):
    id: Optional[int] = None
    form_id: Optional[int] = None
    package_container: Optional[PackagingType] = None
    sales_price_code_id: Optional[int] = None

    sales_price_code: Optional[SalesPriceCodeDTO] = None
    # product_barcode: Optional[List[Optional[str]]] = []
    parent_package_id: Optional[int] = None
    quantity_per_parent: Optional[int] = None

    # @field_serializer("product_barcode")
    # def serialize_barcode(self, barcodes):
    #     return [b.code if hasattr(b, "code") else b for b in barcodes]

    class Config:
        from_attributes = True


class DrugFormDTO(BaseModel):
    id: Optional[int] = None
    drug_id: Optional[int] = None
    drug_form: Optional[Form] = None
    form_packages: Optional[List[PharmDrugPackageDTO]] = []

    class Config:
        from_attributes = True


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
        from_attributes = True


class DrugDTO(BaseModel):
    drug_info: Optional[DrugInfoDTO] = None
    product: Optional[ProductDTO] = None
    group_tags: Optional[List[DrugGroupTagDTO]] = None

    drug_forms: Optional[List[DrugFormDTO]] = None

    class Config:
        from_attributes = True
        use_enum_values = True  # To store enum values properly
