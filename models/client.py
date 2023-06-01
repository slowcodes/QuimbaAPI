import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from sqlalchemy.orm import relationship

from db import Base
from enum import Enum


class MaritalStatus(str, Enum):
    SINGLE = 'Single'
    MARRIED = 'Married'
    DIVORCED = 'Divorced'
    SEPARATED = 'Separated'
    CONFIDENTIAL = 'Prefer not to say'


class Sex(str, Enum):
    MALE = 'Male'
    FEMALE = 'Female'


class People(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    photo = Column(BLOB)
    first_name = Column(String(30))
    last_name = Column(String(30))
    middle_name = Column(String(30))
    sex = Column(SqlEnum(Sex))
    marital_status = Column(SqlEnum(MaritalStatus))
    date_of_birth = Column(Date)
    blood_group = Column(String(2))
    email = Column(String(50), unique=True)
    phone = Column(String(25))  # Made 25 due to faker generator. should be 11
    address = Column(String(100))
    lga_id = Column(Integer, ForeignKey("lga.id", ondelete='CASCADE'))
    occupation_id = Column(Integer, ForeignKey("occupation.id", ondelete='CASCADE'))
    enrollment_date = Column(Date, default=datetime.date.today())
    # lga = relationship("Lga", back_populates="lga", cascade="all, delete")


class OrganizationPeople(Base):
    __tablename__ = "people_organisation"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete='CASCADE'))
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete='CASCADE'))


class State(Base):
    __tablename__ = "state"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(30), unique=True, index=True)


class Lga(Base):
    __tablename__ = "lga"

    id = Column(Integer, primary_key=True, index=True)
    lga = Column(String(25))
    state_id = Column(Integer, ForeignKey("state.id", ondelete='CASCADE'))


class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20))
    email = Column(String(50))
    phone = Column(String(11))
    address = Column(String(50))
    lga_id = Column(Integer, ForeignKey("lga.id", ondelete='CASCADE'))


class Occupation(Base):
    __tablename__ = "occupation"

    id = Column(Integer, primary_key=True, index=True)
    occupation = Column(Text)
