from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from db import Base
from enum import Enum
from models.supply import Supplier
from models import transaction


class BusinessSales(Base):
    __tablename__ = "Sales"

    id = Column(Integer, primary_key=True, index=True)
    price_code = Column(String(30))


class Form(str, Enum):
    TABLETS = 'Tablet'
    SYRUP = 'Syrup'


class Drugs_Group(Base):
    __tablename__ = "Pharmacy_Drug_Group"
    id = Column(Integer, primary_key=True, index=True)
    Category = Column(String(30))


class Drugs_Group_Tag(Base):
    __tablename__ = "Pharmacy_Drug_Group_Tag"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("Pharmacy_Drug_Group.id", ondelete='CASCADE'))
    drug_id = Column(Integer, ForeignKey("Pharmacy_Drug.id", ondelete='CASCADE'))


class Drugs(Base):
    __tablename__ = "Pharmacy_Drug"

    id = Column(Integer, primary_key=True, index=True)
    retail_form = Column(SqlEnum(Form))


class Supply(Base):
    __tablename__ = "Pharmacy_Supply"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("Pharmacy_Drug.id", ondelete='CASCADE'))
    supplier_id = Column(Integer, ForeignKey("Supply.id", ondelete='CASCADE'))
    manufacture_date = Column(Date)
    expiry_date = Column(Date)
    quantity = Column(Double)
