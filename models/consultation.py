import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from sqlalchemy.orm import relationship
from db import Base
from models.client import Severity
from models.users import User

class Vitals(Base):
    __tablename__ = "Vitals"
    id = Column(Integer, primary_key=True, index=True)

    temperature = Column(Double)
    bmi = Column(Double)
    blood_pressure = Column(String(10))
    weight = Column(Double)
    height = Column(Double)
    created_at = Column(DateTime, default=datetime.date.today())
    client_id = (Integer, ForeignKey("client.id", ondelete='CASCADE'))


class Schedule(Base):
    __tablename__ = "Consultation_Schedule"
    id = Column(Integer, primary_key=True, index=True)

    date_of_consultation = Column(Date)
    specialist = Column(Integer, ForeignKey("Specialist.id", ondelete='CASCADE'))


class Specialism(Base):
    __tablename__ = "Department"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(50))


class Specialist(Base):
    __tablename__ = "Specialist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete='CASCADE'))
    specialism = Column(Integer, ForeignKey("Department.id", ondelete='CASCADE'))


class QueueStatus(str, Enum):
    WAITING = 'Waiting'
    PROCESSED = 'Processed'
    PROCESSING = 'Processing'
    CANCELLED = 'Cancelled'

class ConsultationQueue(Base):
    __tablename__ = "Consultation_Queue"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("Consultation_Schedule.id", ondelete='CASCADE'))
    scheduled_at = Column(Date, default=datetime.date.today())
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.PROCESSING)
    booking_id = Column(Integer, ForeignKey("Service_Booking.id", ondelete='CASCADE'))


class Symptom(Base):
    __tablename__ = 'Symptom'

    id = Column(Integer, primary_key=True, index=True)
    symptom = Column(String(150))


class PresentingSymptomsFrequency(str, Enum):
    Low = 'New Occurranc'
    Medium = 'Medium'
    High = 'High'


class SymptomFrequency(str, Enum):
    UNKOWN = 'UNKNOWN'
    REOCCURING = 'Reoccuring'
    NOVEL = 'NOVEL'


class Presenting_Symptom(Base):
    __tablename__ = 'Presenting_Symptoms'

    id = Column(Integer, primary_key=True, index=True)
    clinical_examination_id = Column(Integer, ForeignKey("Clinical_Examination.id", ondelete='CASCADE'))
    symptom_id = Column(Integer, ForeignKey("Symptom.id", ondelete='CASCADE'))
    severity = Column(SqlEnum(Severity))
    frequency = Column(SqlEnum(SymptomFrequency))


class ClinicalExaminations(Base):
    __tablename__ = 'Clinical_Examination'

    id = Column(Integer, primary_key=True, index=True)
    presenting_complaints = Column(String(150))
    complaints_complaint_ = Column(String(150))
    conducted_at = Column(Date)
