from typing import Optional, List

from dtos.client.lifestyle import ClientLifestyleDTO
from models.client import LifestyleFactor, ClientLifestyle
from sqlalchemy.orm import Session

from repos.client.icd10_repository import Icd10Repository


class ClientLifestyleRepository:
    def __init__(self, db: Session):
        self.db = db
        self.icd_repository = Icd10Repository(db)

    def submit_lifestyle(self, data: ClientLifestyleDTO):
        """
        Submit lifestyle data for a patient using normalized factor-value model.
        """
        # Fetch all relevant factors in one query to reduce DB hits
        factor_names = list(data.lifestyles.keys())
        factors = self.db .query(LifestyleFactor).filter(LifestyleFactor.name.in_(factor_names)).all()
        factor_map = {f.name: f for f in factors}

        missing_factors = [name for name in factor_names if name not in factor_map]
        if missing_factors:
            return {"error": f"Invalid lifestyle factors: {', '.join(missing_factors)}"}

        # Upsert each lifestyle value
        for name, value in data.lifestyles.items():
            factor = factor_map[name]

            # Check if a record exists
            existing = self.session.query(ClientLifestyle).filter_by(
                patient_id=data.patient_id,
                factor_id=factor.id
            ).first()

            if existing:
                existing.value = str(value)  # update
            else:
                record = ClientLifestyle(
                    patient_id=data.patient_id,
                    factor_id=factor.id,
                    value=str(value)
                )
                self.session.add(record)

        self.db.commit()

        return {"message": "Lifestyle data submitted successfully"}

    # -----------------------
    # CREATE
    # -----------------------
    def create(self, patient_id: int, factor_id: int, value: Optional[str] = None) -> ClientLifestyleDTO:
        obj = ClientLifestyle(patient_id=patient_id, factor_id=factor_id, value=value)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return ClientLifestyleDTO.from_orm(obj)

    # -----------------------
    # READ
    # -----------------------
    def get_by_id(self, lifestyle_id: int) -> Optional[ClientLifestyleDTO]:
        obj = self.db.query(ClientLifestyle).filter(ClientLifestyle.id == lifestyle_id).first()
        return ClientLifestyleDTO.from_orm(obj) if obj else None

    def get_by_patient(self, patient_id: int) -> List[ClientLifestyleDTO]:
        objs = (
            self.db.query(ClientLifestyle)
            .join(LifestyleFactor)
            .filter(ClientLifestyle.patient_id == patient_id)
            .all()
        )
        styles = [ClientLifestyleDTO.from_orm(obj) for obj in objs]

        for life_style in styles:
            if life_style.factor.id == 1 or life_style.factor.id == 6 or life_style.factor.id==7 or life_style.factor.id==8:
                # get icd10 data
                icd_ids = [int(x) for x in life_style.value.split(",") if x.isdigit()]
                val = []
                for icd_id in icd_ids:
                    icd_data = self.icd_repository.get(icd_id)
                    if icd_data:
                        val.append(icd_data)
                life_style.value = val

        return styles



    # -----------------------
    # UPDATE
    # -----------------------
    def update(self, lifestyle_id: int, value: Optional[str] = None, factor_id: Optional[int] = None) -> Optional[ClientLifestyleDTO]:
        obj = self.db.query(ClientLifestyle).filter(ClientLifestyle.id == lifestyle_id).first()
        if not obj:
            return None
        if value is not None:
            obj.value = value
        if factor_id is not None:
            obj.factor_id = factor_id
        self.db.commit()
        self.db.refresh(obj)
        return ClientLifestyleDTO.from_orm(obj)

    # -----------------------
    # DELETE
    # -----------------------
    def delete(self, lifestyle_id: int) -> bool:
        obj = self.db.query(ClientLifestyle).filter(ClientLifestyle.id == lifestyle_id).first()
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
