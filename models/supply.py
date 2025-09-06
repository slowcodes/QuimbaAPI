from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, \
    BLOB, BIGINT
from db import Base
from enum import Enum

from models.consultation import SoftDeleteMixin
from models.pharmacy import Form
from models.transaction import Transaction


class Supplier(Base, SoftDeleteMixin):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organization.id", ondelete="cascade"))


class Supply(Base, SoftDeleteMixin):
    __tablename__ = "supply"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("supplier.id", ondelete="cascade"))
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))
    pharmacy_id = Column(Integer, ForeignKey("pharmacy.id", ondelete="cascade")) # This is organization or store


class SupplyDetail(Base, SoftDeleteMixin):
    __tablename__ = "supply_detail"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="cascade"))
    manufacture_date = Column(Date)
    expiry_date = Column(Date)
    quantity = Column(Double)
    supply_id = Column(Integer, ForeignKey("supply.id", ondelete="cascade"))  # FIXED
    product_packaging_id = Column(Integer, ForeignKey("product_package.id", ondelete="cascade"))  # FIXED


class SupplyPharmDetail(Base, SoftDeleteMixin):
    __tablename__ = "supply_pharm_detail"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supply_id = Column(Integer, ForeignKey("supply.id", ondelete="cascade"))
    drug_form = Column(SqlEnum(Form))
