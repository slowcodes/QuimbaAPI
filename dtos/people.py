from enum import Enum
from typing import List, Optional, Dict

from pydantic import EmailStr, BaseModel, Field, validator
from datetime import date, datetime
from models.client import Sex, MaritalStatus, VitalType, ProfTitle


class LocalityDTO(BaseModel):
    lga_id: Optional[int] = None
    state_id: Optional[int] = None
    state: Optional[str] = None
    lga: Optional[str] = None


class StateDTO(BaseModel):
    id: Optional[int] = None
    state: Optional[str] = None

    class Config:
        from_attributes = True


class LgaDTO(BaseModel):
    id: Optional[int] = None
    lga: Optional[str] = None

    state: Optional[StateDTO] = None

    class Config:
        from_attributes = True


class OccupationDTO(BaseModel):
    id: Optional[int] = None
    occupation: Optional[str] = None

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class BasicPersonDTO(BaseModel):
    id: int
    title: Optional[ProfTitle] = ProfTitle.Mr
    first_name: str
    last_name: str
    sex: Optional[Sex] = None

    class Config:
        from_attributes = True


class OrganizationPeopleDTO(BaseModel):
    id: int
    organization_id: int
    person_id: int
    organization: OrganisationDTO

    class Config:
        from_attributes = True


class PersonDTO(BaseModel):
    id: Optional[int] = None
    title: Optional[ProfTitle] = ProfTitle.Mr
    first_name: str = Field(..., min_length=1, max_length=30)
    middle_name: Optional[str] = Field(None, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    sex: Sex
    title: Optional[ProfTitle] = ProfTitle.Mr
    email: Optional[str] = None
    phone: str = Field(..., min_length=0, max_length=11)

    organization_people: Optional[List[OrganizationPeopleDTO]] = []

    class Config:
        from_attributes = True


class BasicClientDTO(BaseModel):
    id: int
    person_id: Optional[int] = None
    occupation: Optional[OccupationDTO] = None
    person: Optional[PersonDTO] = None
    lga: Optional[LgaDTO] = None
    marital_status: Optional[str] = None
    date_of_birth: Optional[date] = None

    class Config:
        from_attributes = True


class ClientDTO(BaseModel):
    id: Optional[int] = None
    marital_status: MaritalStatus
    date_of_birth: date
    blood_group: Optional[str] = Field(..., max_length=3)
    address: Optional[str] = Field(..., max_length=100)
    locality: Optional[LocalityDTO] = None
    lga: Optional[LgaDTO] = None
    occupation: Optional[OccupationDTO] = None
    photo: Optional[bytes] = None
    person: Optional[PersonDTO] = None
    organization: Optional[OrganisationDTO] = None

    # @validator("locality", pre=True, always=True)
    # def validate_locality(cls, v):
    #     if v:
    #         if not v.get("lga") or not v.get("state"):
    #             raise ValueError("Locality must have both 'lga' and 'state' if provided.")
    #     return v
    #
    # @validator("occupation", pre=True, always=True)
    # def validate_occupation(cls, value):
    #     if value and not value.get("id"):  # getattr(value, 'occupation', None):
    #         raise ValueError("Occupation must have 'occupation' if provided.")
    #     return value

    # @validator("organization")
    # def validate_organization(cls, value):
    #     if value and not getattr(value, 'name', None):
    #         raise ValueError("Organization must have 'name' if provided.")
    #     return value

    class Config:
        from_attributes = True


# class ClientLifestyleDTO(BaseModel):
#     patient_id: int
#     lifestyles: Dict[str, str]


class ReferralDTO(BaseModel):
    id: Optional[int] = None
    person: Optional[PersonDTO]  # Do not use BasicPersonDTO
    person_id: Optional[int] = None

    class Config:
        from_attributes = True


class BasicReferralDTO(BaseModel):
    id: int
    person_id: int
    person: BasicPersonDTO

    class Config:
        from_attributes = True


class ReferralResponseDTO(BaseModel):
    total: int
    data: List[ReferralDTO]


class VitalsDTO(BaseModel):
    id: int
    vital_type: VitalType
    vital_value: str
    created_at: datetime
    client_id: int

    class Config:
        from_attributes = True


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
