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
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(EmailStr, unique=True, index=True)
    password = Column(String(50))
    created_at = Column(DateTime, default=datetime.now())
    last_modified = Column(DateTime, default=datetime.now())
    last_login = Column(DateTime, default=datetime.now())
    status = AccountStatus = AccountStatus.ACTIVE
    person_id = (Integer, ForeignKey("person.id"))
