from typing import Optional

from pydantic import BaseModel

from models.admission import BedRoomStatus


class BedBaseDTO(BaseModel):
    ward_id: int
    bed_number: str
    status: Optional[BedRoomStatus] = None

    class Config:
        from_attributes = True


class BedCreateDTO(BedBaseDTO):
    pass


class BedUpdateDTO(BaseModel):
    bed_number: Optional[str] = None
    status: Optional[BedRoomStatus] = None
    ward_id: Optional[int] = None

    class Config:
        from_attributes = True


class BedDTO(BedBaseDTO):
    id: Optional[int] = None
