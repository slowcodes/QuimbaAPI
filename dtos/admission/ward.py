from typing import List, Optional

from pydantic import BaseModel

from dtos.admission.bed import BedCreateDTO, BedDTO
from dtos.admission.room import RoomCreateDTO, RoomDTO
from models.admission import WardType


class WardBaseDTO(BaseModel):
    name: str
    description: Optional[str] = None
    ward_type: WardType = WardType.General

    class Config:
        from_attributes = True


class WardCreateDTO(WardBaseDTO):
    beds: Optional[List[BedCreateDTO]] = None
    rooms: Optional[List[RoomCreateDTO]] = None


class WardUpdateDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ward_type: Optional[WardType] = None

    class Config:
        from_attributes = True


class WardDTO(WardBaseDTO):
    id: Optional[int] = None
    beds: Optional[List[BedDTO]] = None
    rooms: Optional[List[RoomDTO]] = None
