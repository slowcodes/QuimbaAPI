from typing import Optional, List

from pydantic import BaseModel

from dtos.people import OrganisationDTO
from dtos.pharmacy.drug import DrugDTO
from dtos.transaction import PaymentDTO
from models.pharmacy import Form


class SupplyCartItemDTO(BaseModel):
    id: Optional[int] = None
    package_container: int
    supply_quantity: int
    buying_price: float
    drug_form: Optional[Form] = None
    drug: DrugDTO
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None


class SupplyDTO(BaseModel):
    id: Optional[int] = None
    cart: Optional[List[SupplyCartItemDTO]]
    supplier: OrganisationDTO
    pharmacy: OrganisationDTO
    discount: float = 0.0
    payment: Optional[List[PaymentDTO]]

