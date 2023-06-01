from pydantic import EmailStr
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from db import Base
from enum import Enum
from datetime import datetime


class AccountStatus(str, Enum):
    ACTIVE = 'Active'
    SUSPENDED = 'Suspended'
    DELETED = 'Deleted'
    INACTIVE = 'Inactive'


class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, index=True)
    password = Column(String(50))
    created_at = Column(DateTime, default=datetime.now())
    last_modified = Column(DateTime, default=datetime.now())
    last_login = Column(DateTime, default=datetime.now())
    status = AccountStatus = AccountStatus.ACTIVE
    person_id = (Integer, ForeignKey("person.id"))


class UserBase(Base):
    __tablename__ = 'Users_Classification'
    id = Column(Integer, primary_key=True, index=True)
    classification = Column(String(50)) # e.g physician, nurse, lab scientist