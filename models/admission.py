from sqlalchemy import Enum as SAEnum, Column, Integer, ForeignKey, String, Enum as SqlEnum, DateTime
from sqlalchemy.orm import relationship

from db import Base
from enum import Enum


class Admission(Base):
    __tablename__ = 'admission'
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer)
    bed_id = Column(Integer)
    patient_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    admission_date = Column(DateTime, nullable=False)
    reason = Column(String(200), nullable=False)


class AdmissionLabServices(Base):
    __tablename__ = 'admission_lab_services'
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admission.id", ondelete="cascade"))
    lab_service_queue_id = Column(Integer, ForeignKey("lab_service_queue.id", ondelete="cascade"))

    lab_service_queue = relationship("LabServicesQueue", back_populates="admission_lab_services", uselist=True)


class AdmissionConsultationBookings(Base):
    __tablename__ = 'admission_consultation_bookings'
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admission.id", ondelete="cascade"))
    consultation_booking_id = Column(Integer, ForeignKey("consultation_queue.id", ondelete="cascade"))

    consultation = relationship("ConsultationQueue", back_populates="admission_consultation_bookings", uselist=True)


class AdmissionPrescriptions(Base):
    __tablename__ = 'admission_prescription'
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admission.id", ondelete="cascade"))
    prescription_id = Column(Integer, ForeignKey("prescription.id", ondelete="cascade"))

    prescription = relationship("Prescription", back_populates="admission_prescriptions", uselist=True)


class WardType(str, Enum):
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
    ward_type = Column(SqlEnum(WardType), default=WardType.General)


class DischargeType(str, Enum):
    Routine = 'Routine'
    Emergency = 'Emergency'
    Transfer = 'Transfer'
    Self = 'Self'
    Others = 'Others'


class AdmissionDischarge(Base):
    __tablename__ = 'admission_discharge'
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admission.id", ondelete="cascade"))
    discharge_date = Column(DateTime, nullable=False)
    discharge_type = Column(SqlEnum(DischargeType), default=DischargeType.Routine)
    notes = Column(String(200), nullable=True)


class Bed(Base):
    __tablename__ = 'admission_bed'
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("admission_ward.id", ondelete="cascade"))
