from typing import Optional

from sqlalchemy.orm import Session

from dtos.admission import WardCreateDTO, WardDTO, WardUpdateDTO
from models.admission import Bed, Rooms, Ward


class WardRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_ward(self, ward: WardCreateDTO) -> WardDTO:
        ward_data = ward.dict(exclude={"beds", "rooms"})
        db_ward = Ward(**ward_data)
        self.session.add(db_ward)
        self.session.flush()

        for bed in ward.beds or []:
            bed_data = bed.dict()
            bed_data["ward_id"] = db_ward.id
            self.session.add(Bed(**bed_data))

        for room in ward.rooms or []:
            room_data = room.dict()
            room_data["ward_id"] = db_ward.id
            self.session.add(Rooms(**room_data))

        self.session.commit()
        self.session.refresh(db_ward)
        return WardDTO.from_orm(db_ward)

    def get_ward(self, ward_id: int) -> Optional[WardDTO]:
        ward = (
            self.session.query(Ward)
            .filter(Ward.id == ward_id, Ward.is_deleted.is_(False))
            .first()
        )
        return WardDTO.from_orm(ward) if ward else None

    def get_wards(self, skip: int = 0, limit: int = 100) -> dict:
        query = self.session.query(Ward).filter(Ward.is_deleted.is_(False))
        total = query.count()
        wards = query.offset(skip).limit(limit).all()
        return {
            "data": [WardDTO.from_orm(ward) for ward in wards],
            "total": total,
        }

    def update_ward(self, ward_id: int, ward_update: WardUpdateDTO) -> Optional[WardDTO]:
        ward = (
            self.session.query(Ward)
            .filter(Ward.id == ward_id, Ward.is_deleted.is_(False))
            .first()
        )
        if not ward:
            return None
        for key, value in ward_update.dict(exclude_unset=True).items():
            setattr(ward, key, value)
        self.session.commit()
        self.session.refresh(ward)
        return WardDTO.from_orm(ward)

    def delete_ward(self, ward_id: int) -> bool:
        ward = (
            self.session.query(Ward)
            .filter(Ward.id == ward_id, Ward.is_deleted.is_(False))
            .first()
        )
        if not ward:
            return False
        ward.is_deleted = True
        self.session.commit()
        return True
