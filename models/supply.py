from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from db import Base
from enum import Enum
from models.transaction import Transaction

class Supplier(Base):
    __tablename__ = "Supplier"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(30))
    last_name = Column(String(30))
    address = Column(Text)
    address_landmark = Column(Text)
    lga_id = ForeignKey("lga.id", ondelete='CASCADE')
    phone_number = Column(String(11))
    company = Column(String(30))


class Supplies(Base):
    __tablename__ = "Supply"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("Supplier.id", ondelete='CASCADE'))
    transaction_id = Column(Integer, ForeignKey("Transaction.id", ondelete='CASCADE'))