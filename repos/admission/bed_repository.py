from typing import Optional

from sqlalchemy.orm import Session

from dtos.admission import BedCreateDTO, BedDTO, BedUpdateDTO
from models.admission import Bed


class BedRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_bed(self, bed: BedCreateDTO) -> BedDTO:
        db_bed = Bed(**bed.dict())
        self.session.add(db_bed)
        self.session.commit()
        self.session.refresh(db_bed)
        return BedDTO.from_orm(db_bed)

    def get_bed(self, bed_id: int) -> Optional[BedDTO]:
        bed = (
            self.session.query(Bed)
            .filter(Bed.id == bed_id, Bed.is_deleted.is_(False))
            .first()
        )
        return BedDTO.from_orm(bed) if bed else None

    def get_beds(self, skip: int = 0, limit: int = 100, ward_id: int = 0) -> dict:
        query = self.session.query(Bed).filter(Bed.is_deleted.is_(False))
        if ward_id:
            query = query.filter(Bed.ward_id == ward_id)
        total = query.count()
        beds = query.offset(skip).limit(limit).all()
        return {
            "data": [BedDTO.from_orm(bed) for bed in beds],
            "total": total,
        }

    def update_bed(self, bed_id: int, bed_update: BedUpdateDTO) -> Optional[BedDTO]:
        bed = (
            self.session.query(Bed)
            .filter(Bed.id == bed_id, Bed.is_deleted.is_(False))
            .first()
        )
        if not bed:
            return None
        for key, value in bed_update.dict(exclude_unset=True).items():
            setattr(bed, key, value)
        self.session.commit()
        self.session.refresh(bed)
        return BedDTO.from_orm(bed)

    def delete_bed(self, bed_id: int) -> bool:
        bed = (
            self.session.query(Bed)
            .filter(Bed.id == bed_id, Bed.is_deleted.is_(False))
            .first()
        )
        if not bed:
            return False
        bed.is_deleted = True
        self.session.commit()
        return True
