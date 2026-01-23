from typing import Optional

from sqlalchemy.orm import Session

from dtos.admission import RoomCreateDTO, RoomDTO, RoomUpdateDTO
from models.admission import Rooms


class RoomRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_room(self, room: RoomCreateDTO) -> RoomDTO:
        db_room = Rooms(**room.dict())
        self.session.add(db_room)
        self.session.commit()
        self.session.refresh(db_room)
        return RoomDTO.from_orm(db_room)

    def get_room(self, room_id: int) -> Optional[RoomDTO]:
        room = self.session.query(Rooms).filter(Rooms.id == room_id).first()
        return RoomDTO.from_orm(room) if room else None

    def get_rooms(self, skip: int = 0, limit: int = 100, ward_id: int = 0) -> dict:
        query = self.session.query(Rooms)
        if ward_id:
            query = query.filter(Rooms.ward_id == ward_id)
        total = query.count()
        rooms = query.offset(skip).limit(limit).all()
        return {
            "data": [RoomDTO.from_orm(room) for room in rooms],
            "total": total,
        }

    def update_room(self, room_id: int, room_update: RoomUpdateDTO) -> Optional[RoomDTO]:
        room = self.session.query(Rooms).filter(Rooms.id == room_id).first()
        if not room:
            return None
        for key, value in room_update.dict(exclude_unset=True).items():
            setattr(room, key, value)
        self.session.commit()
        self.session.refresh(room)
        return RoomDTO.from_orm(room)

    def delete_room(self, room_id: int) -> bool:
        room = self.session.query(Rooms).filter(Rooms.id == room_id).first()
        if not room:
            return False
        self.session.delete(room)
        self.session.commit()
        return True
