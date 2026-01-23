from typing import Optional

from pydantic import BaseModel

from models.admission import BedRoomStatus


class RoomBaseDTO(BaseModel):
    ward_id: int
    room_number: str
    capacity: int
    description: Optional[str] = None
    status: Optional[BedRoomStatus] = None

    class Config:
        from_attributes = True


class RoomCreateDTO(RoomBaseDTO):
    pass


class RoomUpdateDTO(BaseModel):
    ward_id: Optional[int] = None
    room_number: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    status: Optional[BedRoomStatus] = None

    class Config:
        from_attributes = True


class RoomDTO(RoomBaseDTO):
    id: Optional[int] = None
