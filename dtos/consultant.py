from typing import Optional, List

from pydantic import BaseModel
from datetime import date

from dtos.auth import UserDTO


class ScheduleDTO(BaseModel):
    date_of_consultation: date
    specialist: int

    class Config:
        orm_mode = True
        from_attributes = True


class SpecialistDTO(BaseModel):
    user_id: int
    specialism: int

    class Config:
        orm_mode = True
        from_attributes = True


class SpecialismDTO(BaseModel):
    id: Optional[int]
    department: str
    specialist_title: str

    class Config:
        orm_mode = True
        from_attributes = True


class ConsultantDTO(BaseModel):
    id: Optional[int] = None
    user: UserDTO
    title: str
    specializations: List[SpecialismDTO] = []

    class Config:
        orm_mode = True
        from_attributes = True

