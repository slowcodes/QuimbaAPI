import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from models.pharmacy import Drugs
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


# class BloodGroup(str, Enum):
# "A+" = "A+"
# "FEMALE" = "Female"


class Client(Base):
    __tablename__ = "Client"

    id = Column(Integer, primary_key=True, index=True)
    photo = Column(BLOB)
    first_name = Column(String(30))
    last_name = Column(String(30))
    middle_name = Column(String(30))
    sex = Column(SqlEnum(Sex))
    marital_status = Column(SqlEnum(MaritalStatus))
    date_of_birth = Column(Date)
    blood_group = Column(String(3))
    email = Column(String(50), unique=True)
    phone = Column(String(25))  # Made 25 due to faker generator. should be 11
    address = Column(String(100))
    lga_id = Column(Integer, ForeignKey("Lga.id", ondelete='CASCADE'))
    occupation_id = Column(Integer, ForeignKey("Occupation.id", ondelete='CASCADE'))
    enrollment_date = Column(Date, default=datetime.date.today())
    # lga = relationship("Lga", back_populates="lga", cascade="all, delete")


class OrganizationPeople(Base):
    __tablename__ = "people_organisation"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    organization_id = Column(Integer, ForeignKey("Organization.id", ondelete='CASCADE'))


class State(Base):
    __tablename__ = "State"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(30), unique=True, index=True)


class Lga(Base):
    __tablename__ = "Lga"

    id = Column(Integer, primary_key=True, index=True)
    lga = Column(String(25))
    state_id = Column(Integer, ForeignKey("State.id", ondelete='CASCADE'))


class Organization(Base):
    __tablename__ = "Organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20))
    email = Column(String(50))
    phone = Column(String(11))
    address = Column(String(50))
    lga_id = Column(Integer, ForeignKey("Lga.id", ondelete='CASCADE'))


class Occupation(Base):
    __tablename__ = "Occupation"

    id = Column(Integer, primary_key=True, index=True)
    occupation = Column(Text)


class Severity(str, Enum):
    Low = 'Low'
    Medium = 'Medium'
    High = 'High'


class DrugAllergy(Base):
    __tablename__ = 'DrugAllergy'

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("Pharmacy_Drug.id", ondelete='CASCADE'))
    detail = Column(String(100))
    risk_severity = Column(SqlEnum(Severity))
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))


class FoodAllergy(Base):
    __tablename__ = 'Food_Allergy'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    food = Column(String(100))
    detail = Column(String(100))
    risk_severity = Column(SqlEnum(Severity))
