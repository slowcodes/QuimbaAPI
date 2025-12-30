import datetime

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, Float, String,
    DateTime, Date, Text, BLOB, BIGINT, Double, Index
)
from sqlalchemy.orm import relationship
from db import Base
from models.mixins import SoftDeleteMixin


class BusinessSales(Base, SoftDeleteMixin):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey("pharmacy_drug_form_package.id", ondelete="cascade"))
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade")) # Causes cyclic depenency issues. Re-evaluate related usage.
    sale_service_id = Column(Integer, ForeignKey("service_booking.id", ondelete="cascade"))
    per_package_sales_code_id = Column(Integer, ForeignKey("sales_price_code.id"))
    quantity = Column(Integer)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="cascade"))

    package = relationship("PharmDrugFormPackage", back_populates="sales")
    # transaction = relationship("Transaction", back_populates="sales")
    sales_service = relationship("ServiceBooking", back_populates="business_sales")
    sales_price_code = relationship("SalesPriceCode", back_populates="sale")
    product = relationship("Product", back_populates="sales")
    dispensed_prescriptions = relationship("DispensedPrescriptionDetail", back_populates="sale")


class SalesPriceCode(Base):
    __tablename__ = "sales_price_code"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    selling_price = Column(Double)
    buying_price = Column(Double)
    # packaging_id = Column(Integer) # Not necessary as it will be recorded in sales
    date_created = Column(DateTime,
                          default=datetime.datetime.utcnow)  # tracking date of creation due to product price changes

    product_package = relationship("ProductPackage", back_populates="sales_price_code")
    pharmacy_drug_form_package = relationship("PharmDrugFormPackage", back_populates="sales_price_code")
    sale = relationship("BusinessSales", back_populates="sales_price_code")
