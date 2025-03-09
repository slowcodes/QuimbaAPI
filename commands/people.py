from typing import List, Optional
from pydantic import EmailStr, BaseModel
from datetime import datetime, date, time, timedelta

from models.client import Sex, MaritalStatus, VitalType


class LocalityDTO(BaseModel):
    lga_id: Optional[int]
    state_id: Optional[int]
    state: Optional[str]
    lga: Optional[str]


class OccupationDTO(BaseModel):
    id: Optional[int]
    occupation: Optional[str]


class OrganisationDTO(BaseModel):
    id: Optional[int]
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]


class ClientCommand(BaseModel):
    first_name: str
    middle_name: str
    last_name: str
    sex: Sex
    marital_status: MaritalStatus
    date_of_birth: date
    blood_group: str
    email: EmailStr
    phone: str
    address: str
    locality: Optional[LocalityDTO] = None
    occupation: Optional[OccupationDTO] = None
    photo: Optional[bytes] = None
    organization: Optional[OrganisationDTO] = None

    def validate_optional_fields(self):
        if self.locality:
            if not self.locality.lga or not self.locality.state:
                raise ValueError("Locality must have both 'lga' and 'state' if provided.")
        if self.occupation:
            if not self.occupation.occupation:
                raise ValueError("Occupation must have 'occupation' if provided.")
        if self.organization:
            if not self.organization.name:
                raise ValueError("Organization must have 'name' if provided.")


class UserDTO(BaseModel):
    username: str
    id: int
    password_hash: str


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
        orm_mode = True
