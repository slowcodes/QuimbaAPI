
from typing import List
from pydantic import EmailStr, BaseModel
from datetime import datetime, date, time, timedelta

from models.people import Sex, MaritalStatus


class Client (BaseModel):
    photo: bytes
    first_name: str
    last_name: str
    sex: Sex
    marital_status: MaritalStatus
    date_of_birth: date
    blood_group: str
    email: EmailStr
    phone: str
    address: str
    lga_id: int
    occupation: str

