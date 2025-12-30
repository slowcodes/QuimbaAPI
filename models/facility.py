from enum import Enum

from sqlalchemy import Column, Integer, Enum as SqlEnum, ForeignKey

from db import Base
from models.consultation import SoftDeleteMixin


class FacilityType(str, Enum):
    Bed = 'Bed'
    Wards = 'Wards'
    Room = 'Room'
    Equipment = 'Equipment'


class RateType(str, Enum):
    PerDay = 'PerDay'
    PerHour = 'PerHour'
    PerWeek = 'PerWeek'
    PerMonth = 'PerMonth'


class Facility(Base, SoftDeleteMixin):
    __tablename__ = "facility"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    facility_type = Column(SqlEnum(FacilityType), nullable=False)
    rate_type = Column(SqlEnum(RateType), nullable=False)
    price_code = Column(Integer, ForeignKey("service_price_code.id", ondelete="cascade"))  # Price of the facility
