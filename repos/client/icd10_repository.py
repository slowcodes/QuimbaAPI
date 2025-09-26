from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import or_

from dtos.client.icd10 import Icd10DTO, Icd10Response
from models.client import Icd10


class Icd10Repository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, icd10_id: int) -> Optional[Icd10DTO]:
        obj = self.db.query(Icd10).filter(Icd10.id == icd10_id).first()
        return Icd10DTO.from_orm(obj) if obj else None

    def get_by_code(self, head_code: str) -> Optional[Icd10DTO]:
        obj = self.db.query(Icd10).filter(Icd10.head_code == head_code).first()
        return Icd10DTO.from_orm(obj) if obj else None

    def list(self, skip: int = 0, limit: int = 100) -> List[Icd10Response]:
        objs = self.db.query(Icd10).offset(skip).limit(limit).all()
        return Icd10Response(
            data=[Icd10DTO.from_orm(obj) for obj in objs],
            total=self.db.query(Icd10).count()
        )

    def search(self, query: str, skip: int = 0, limit: int = 50) -> List[Icd10Response]:
        """Search ICD-10 codes by partial code or name."""
        objs = (
            self.db.query(Icd10)
            .filter(
                or_(
                    Icd10.head_code.ilike(f"%{query}%"),
                    Icd10.name.ilike(f"%{query}%"),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        total = self.db.query(Icd10).filter(
            or_(
                Icd10.head_code.ilike(f"%{query}%"),
                Icd10.name.ilike(f"%{query}%"),
            )
        ).count()
        data = [Icd10DTO.from_orm(obj) for obj in objs]
        return Icd10Response(total=total, data=data)




