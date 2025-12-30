from datetime import datetime
from operator import and_
from typing import Optional, List

from sqlmodel import Session

from dtos.pharmacy.dispensed import DispensedPrescriptionRead
from dtos.pharmacy.prescription import PrescriptionDTO
from models.pharmacy import DispensedPrescriptionDetail, Prescription, PrescriptionDetail
from models.product import Product
from models.sales import SalesPriceCode
from models.services.services import ServiceBooking


class DispensedDrugRepository:
    """
    Repository for managing DispensedDrug records in the database.
    """

    def __init__(self, db: Session):
        self.db = db

    #
    # def add_dispensed_drug(self, drug_data: DispensedDrugCreate) -> DispensedDrugRead:
    #     """
    #     Add a new dispensed drug record and return DTO.
    #     """
    #     dispensed_drug = DispensedDrugs(**drug_data.dict())
    #     self.db.add(dispensed_drug)
    #     self.db.commit()
    #     self.db.refresh(dispensed_drug)
    #     return DispensedDrugRead.from_orm(dispensed_drug)
    #
    # def get_dispensary_service_booking(self, transaction_id: int):
    #     """
    #     Retrieve dispensed drugs for a specific transaction ID,
    #     returning a list of DTOs (DispensedDrugRead).
    #     """
    #     cols = [
    #         ServiceBooking.id.label("booking_detail_id"),
    #         Product.product_name.label("lab_service_name"),
    #         SalesPriceCode.id.label("price_code"),
    #         SalesPriceCode.selling_price.label("price"),
    #     ]
    #
    #     dispensed_drugs = (
    #         self.db.query(*cols).select_from(DispensedDrugs)
    #         .join(Prescription, DispensedDrugs.prescription_id == Prescription.id)
    #         .join(PrescriptionDetail, Prescription.id == PrescriptionDetail.prescription_id)
    #         .join(Drug, PrescriptionDetail.drug_id == Drug.id)
    #         .join(Product, Drug.product_id == Product.id)
    #         .join(ServiceBooking, DispensedDrugs.sale_service_id == ServiceBooking.id)
    #         .filter(ServiceBooking.transaction_id == transaction_id)
    #         .all()
    #     )
    #     return dispensed_drugs
    #
    # def get_dispensed_drugs(
    #         self,
    #         skip: int = 0,
    #         limit: int = 10,
    #         start_date: Optional[datetime] = None,
    #         last_date: Optional[datetime] = None,
    # ) -> List[DispensedDrugRead]:
    #     """
    #     Read dispensed drugs with optional filters and pagination,
    #     returning a list of DTOs (DispensedDrugRead).
    #     """
    #     query = self.db.query(DispensedDrugs)
    #
    #     if start_date is not None and last_date is not None:
    #         query = query.filter(
    #             and_(
    #                 DispensedDrugs.dispensed_at >= start_date,
    #                 DispensedDrugs.dispensed_at <= last_date
    #             )
    #         )
    #     elif start_date is not None:
    #         query = query.filter(DispensedDrugs.dispensed_at >= start_date)
    #     elif last_date is not None:
    #         query = query.filter(DispensedDrugs.dispensed_at <= last_date)
    #
    #     # Order and paginate
    #     dispensed_drugs = (
    #         query.order_by(DispensedDrugs.dispensed_at.desc())
    #         .offset(skip)
    #         .limit(limit)
    #         .all()
    #     )
    #
    #     # Convert to Pydantic DTOs
    #     return [DispensedDrugRead.from_orm(drug) for drug in dispensed_drugs]

    def create(self, data: dict) -> DispensedPrescriptionRead:
        dispensed = DispensedPrescriptionDetail(**data)
        self.db.add(dispensed)
        self.db.commit()
        self.db.refresh(dispensed)
        return DispensedPrescriptionRead.from_orm(dispensed)

    def get_by_id(self, id: int):
        return self.db.query(DispensedPrescriptionDetail).filter(DispensedPrescriptionDetail.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(DispensedPrescriptionDetail).offset(skip).limit(limit).all()

    def delete(self, id: int):
        dispensed = self.get_by_id(id)
        if not dispensed:
            return None
        self.db.delete(dispensed)
        self.db.commit()
        return dispensed

    def get_dispensed_prescription(self, skip: int = 0,
                                   limit: int = 0,
                                   client_id: int = 0,
                                   start_date: str = None,
                                   last_date: str = None
                                   ):
        ps = self.db.query(Prescription). \
            join(Prescription.prescriptions). \
            join(PrescriptionDetail.dispensed_prescription_detail). \
            distinct(). \
            all()

        return [PrescriptionDTO.from_orm(presc) for presc in ps]
