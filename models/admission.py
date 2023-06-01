import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from sqlalchemy.orm import relationship
from db import Base


class Admission(Base):
    _tablename__ = 'Admission'
    id = Column(Integer, primary_key=True, index=True)


