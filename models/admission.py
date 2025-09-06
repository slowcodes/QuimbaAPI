import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, Enum as SqlEnum
from db import Base
from enum import Enum


class Admission(Base):
    _tablename__ = 'admission'
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer)
    bed_id = Column(Integer)
    patient_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    admission_date = Column(datetime.datetime, nullable=False)
    reason = Column(String(200), nullable=False)


class WardType(Enum, str):
    General = 'General'
    Private = 'Private'
    ICU = 'ICU'
    Pediatric = 'Pediatric'
    Maternity = 'Maternity'


class Ward(Base):
    __tablename__ = 'admission_ward'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=True)
    ward_type = Column(SqlEnum(WardType), default=WardType.GENERAL)


class DischargeType(Enum, str):
    Routine = 'Routine'
    Emergency = 'Emergency'
    Transfer = 'Transfer'
    Self = 'Self'
    Others = 'Others'


class AdmissionDischarge(Base):
    __tablename__ = 'admission_discharge'
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admission.id", ondelete="cascade"))
    discharge_date = Column(datetime.datetime, nullable=False)
    discharge_type = Column(SqlEnum(DischargeType), default=DischargeType.ROUTINE)
    notes = Column(String(200), nullable=True)


class Bed(Base):
    __tablename__ = 'admission_ded'
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("ward.id", ondelete="cascade"))
