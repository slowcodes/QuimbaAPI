from enum import Enum
from typing import List, Optional

from pydantic import EmailStr, BaseModel, Field, validator
from datetime import date
from models.client import Sex, MaritalStatus, VitalType, ProfTitle


class LocalityDTO(BaseModel):
    lga_id: Optional[int] = None
    state_id: Optional[int] = None
    state: Optional[str] = None
    lga: Optional[str] = None


class OccupationDTO(BaseModel):
    id: Optional[int] = None
    occupation: Optional[str] = None


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
    supplier_id: Optional[int] = None  # conditional based on org type
    pharmacy_id: Optional[int] = None  # conditional based on org type


class PersonDTO(BaseModel):
    id: Optional[int] = None
    first_name: str = Field(..., min_length=1, max_length=30)
    middle_name: Optional[str] = Field(None, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    sex: Sex
    title: Optional[ProfTitle] = ProfTitle.Mr
    email: Optional[EmailStr]
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")


class ClientDTO(PersonDTO):
    marital_status: MaritalStatus
    date_of_birth: date
    blood_group: Optional[str] = Field(..., max_length=3)
    address: Optional[str] = Field(..., max_length=100)
    locality: Optional[LocalityDTO] = None
    occupation: Optional[OccupationDTO] = None
    photo: Optional[bytes] = None
    # user_account: Optional[any] = None
    organization: Optional[OrganisationDTO] = None

    @validator("locality", pre=True, always=True)
    def validate_locality(cls, v):
        if v:
            if not v.get("lga") or not v.get("state"):
                raise ValueError("Locality must have both 'lga' and 'state' if provided.")
        return v

    @validator("occupation", pre=True, always=True)
    def validate_occupation(cls, value):
        if value and not value.get("id"):  # getattr(value, 'occupation', None):
            raise ValueError("Occupation must have 'occupation' if provided.")
        return value

    # @validator("organization")
    # def validate_organization(cls, value):
    #     if value and not getattr(value, 'name', None):
    #         raise ValueError("Organization must have 'name' if provided.")
    #     return value


class ReferralDTO(BaseModel):
    id: Optional[int] = None
    person: Optional[PersonDTO]
    org: Optional[OrganisationDTO] = None


class VitalDTO(BaseModel):
    vital_value: str
    vital_type: VitalType
    client_id: int


class ClientNotificationDTO(BaseModel):
    id: int
    notification: str
    default_sms_msg: str
    default_whatsapp_msg: str
    default_email_msg: str

    # created_at: datetime
    # updated_at: datetime

    class Config:
        from_attributes = True
