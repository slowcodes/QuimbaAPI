from typing import Optional

from pydantic import BaseModel
from enum import Enum


class OrgType(str, Enum):
    Pharmacy = 'Pharmacy'
    Supplier = 'Supplier'
    Others = 'Others'


class OrganisationDTO(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    lga_id: Optional[int] = None
    email: Optional[str] = None
    org_type: Optional[OrgType] = OrgType.Others
    address: Optional[str] = None

    class Config:
        from_attributes = True
