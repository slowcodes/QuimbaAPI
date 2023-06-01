from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Double, Integer, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from db import Base
import datetime
from models import users


class Transaction(Base):
    __tablename__ = "Transaction"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,  ForeignKey("Users.id", ondelete='CASCADE'))
    transaction_date = Column(Date, default=datetime.date.today())
    transaction_time = Column(Date)
    discount = Column(Double)
