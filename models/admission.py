from sqlalchemy import Enum as SAEnum, Column, Integer, ForeignKey, String, Enum as SqlEnum, DateTime
from sqlalchemy.orm import relationship

from db import Base
from models.mixins import SoftDeleteMixin
from enum import Enum


class Admission(Base, SoftDeleteMixin):
    __tablename__ = 'admission'
    id = Column(Integer, primary_key=True, index=True)
    bed_id = Column(Integer, ForeignKey("admission_bed.id", ondelete="cascade"))
    patient_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    admission_date = Column(DateTime, nullable=False)
    reason = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="cascade"))

    lab_services = relationship("AdmissionLabServices", uselist=True)
    consultation_bookings = relationship("AdmissionConsultationBookings", uselist=True)
    prescriptions = relationship("AdmissionPrescriptions", uselist=True)
    user = relationship("User")
    bed = relationship("Bed")


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
    prescription_id = Column(Integer, ForeignKey("pharmacy_prescription.id", ondelete="cascade"))

    prescription = relationship("Prescription", back_populates="admission_prescriptions", uselist=True)


class WardType(str, Enum):
    General = 'General'
    Private = 'Private'
    ICU = 'ICU'
    Pediatric = 'Pediatric'
    Maternity = 'Maternity'


class Ward(Base, SoftDeleteMixin):
    __tablename__ = 'admission_ward'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=True)
    ward_type = Column(SqlEnum(WardType), default=WardType.General)

    rooms = relationship("Rooms", back_populates="ward", uselist=True)
    beds = relationship("Bed", back_populates="ward", uselist=True)


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


class BedRoomStatus(str, Enum):
    Occupied = 'Occupied'
    Free = 'Free'
    Maintenance = 'Maintenance'


class Bed(Base, SoftDeleteMixin):
    __tablename__ = 'admission_bed'
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("admission_ward.id", ondelete="cascade"))
    bed_number = Column(String(50), nullable=False)
    status = Column(SqlEnum(BedRoomStatus), default=BedRoomStatus.Free)

    ward = relationship("Ward", back_populates="beds")
    rooms_containing_bed = relationship("BedInRooms", back_populates="bed", uselist=False)

class Rooms(Base, SoftDeleteMixin):
    __tablename__ = 'admission_ward_room'
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("admission_ward.id", ondelete="cascade"))
    room_number = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    description = Column(String(200), nullable=True)
    status = Column(SqlEnum(BedRoomStatus), default=BedRoomStatus.Free)

    ward = relationship("Ward", back_populates="rooms")
    beds_in_room = relationship("BedInRooms", back_populates="room", uselist=True)


class BedInRooms(Base):
    __tablename__ = 'admission_bed_in_rooms'
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("admission_ward_room.id", ondelete="cascade"))
    bed_id = Column(Integer, ForeignKey("admission_bed.id", ondelete="cascade"))

    room = relationship("Rooms", back_populates="beds_in_room", uselist=True)
    bed = relationship("Bed", back_populates="rooms_containing_bed", uselist=True)
