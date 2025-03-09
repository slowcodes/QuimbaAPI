from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, Enum as SqlEnum, Text, BLOB, Double
from db import Base
from enum import Enum
from models.supply import Supplier
from models import transaction


class Form(str, Enum):
    Tablet = 'Tablet'
    Teaspoon = 'Teaspoon'
    Tablespoon = 'Tablespoon'
    Capsule = 'Capsule'


class SizeType(str, Enum):
    Mass = 'Mass'
    Volume = 'Volume'


class Measure(str, Enum):
    Mg = 'Mg'
    Ml = 'Ml'
    G = 'G'


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
    size_type = Column(SqlEnum(SizeType))
    measure = Column(SqlEnum(Measure))
    product_name = Column(String(40))


class Supply(Base):
    __tablename__ = "Pharmacy_Supply"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("Pharmacy_Drug.id", ondelete='CASCADE'))
    supplier_id = Column(Integer) # Column(Integer, ForeignKey("Supply.id", ondelete='CASCADE'))
    manufacture_date = Column(Date)
    expiry_date = Column(Date)
    quantity = Column(Double)


class Prescription(Base):
    __tablename__ = "Pharmacy_Prescription"
    id = Column(Integer, primary_key=True, index=True)
    prescriber = Column(Integer)  # User Id
    prescription_date = Column(Date)
    client_id = Column(Integer)  # Client Id


class Prescription_Details(Base):
    __tablename__ = "Pharmacy_Prescription_Detail"
    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("Pharmacy_Drug.id", ondelete='CASCADE'))
    prescription_id = Column(Integer, ForeignKey("Pharmacy_Prescription.id", ondelete='CASCADE'))
    quantity = Column(String(20))  # 2
    form = Column(SqlEnum(Form))  # Tablets
    frequency = Column(String(20))  # 12 Hourly, 3X daily
    duration = Column(String(20))  # 7 days
    note = Column(String(30))