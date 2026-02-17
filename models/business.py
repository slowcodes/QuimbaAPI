from sqlalchemy import Integer, Column, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from db import Base
from models.consultation import SoftDeleteMixin


class Business(Base, SoftDeleteMixin):
    __tablename__ = "business_registry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    business_name = Column(String(100), nullable=False)
    rc_number = Column(String(15), nullable=False)

    branches = relationship("BusinessBranch", back_populates="business", uselist=True)


class BranchType(Enum, String):
    HeadOffice = "HeadOffice"
    BranchOffice = "BranchOffice"


class BusinessBranch(Base, SoftDeleteMixin):
    __tablename__ = "business_branch"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey('business_registry.id'), nullable=False)
    address = Column(String(100), nullable=True)
    lga_id = Column(Integer, ForeignKey("lga.id", ondelete="cascade"), nullable=True)
    phone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)

    business = relationship("Business", back_populates="branches", uselist=True)