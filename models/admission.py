import datetime

from sqlalchemy import Column, Integer
from db import Base


class Admission(Base):
    _tablename__ = 'Admission'
    id = Column(Integer, primary_key=True, index=True)


