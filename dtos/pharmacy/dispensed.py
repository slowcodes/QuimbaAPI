from datetime import datetime
from pydantic import BaseModel
from dtos.pharmacy.prescription import PrescriptionDetailDTO
from dtos.sales import BusinessSalesRead


class DispensedPrescriptionBase(BaseModel):
    prescription_detail_id: int
    sales_id: int


class DispensedPrescriptionCreate(DispensedPrescriptionBase):
    pass


class DispensedPrescriptionRead(DispensedPrescriptionBase):
    id: int
    prescription_detail: PrescriptionDetailDTO
    sale: BusinessSalesRead

    class Config:
        from_attributes = True
