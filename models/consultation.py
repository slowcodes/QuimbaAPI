import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, Enum as SqlEnum, Text, BLOB, \
    BIGINT, Index, Double
from sqlalchemy.orm import relationship, aliased
from db import Base
from enum import Enum

from models.client import Severity
from models.lab.lab import QueueStatus


# Base class with soft delete functionality
class SoftDeleteMixin:
    deleted_at = Column(DateTime, default=None, nullable=True)

    def soft_delete(self):
        """Marks the record as deleted by setting the deleted_at timestamp."""
        self.deleted_at = datetime.datetime.utcnow()

    @classmethod
    def query(cls, session):
        """Override the query to exclude soft-deleted records by default."""
        return session.query(cls).filter(cls.deleted_at == None)

    def restore(self):
        """Restores a soft-deleted record by setting deleted_at to None."""
        self.deleted_at = None


# Using the SoftDeleteMixin to implement soft deletes in your models
# class Schedule(Base, SoftDeleteMixin):
#     __tablename__ = "consultant_schedule"
#     id = Column(Integer, primary_key=True, index=True)
#     date_of_consultation = Column(Date)
#     specialist_id = Column(Integer, ForeignKey("consultant_specialist.id", ))
#
#     # Relationship with Specialist
#     specialist = relationship("Specialist", backref="consultant_specialist", lazy='select')
#
#     # Add an index on specialist_id for faster joins and lookups
#     Index('ix_specialist_idx', specialist_id)


class Specialism(Base, SoftDeleteMixin):
    __tablename__ = "consultant_department"
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(50), index=True)
    specialist_title = Column(String(50))


class Specialist(Base, SoftDeleteMixin):
    __tablename__ = "consultant_specialist"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    title = Column(String(50))

    # Relationships
    specializations = relationship("SpecialistSpecialization", backref="specialist", lazy='select')
    consultations = relationship("Consultations", back_populates="creator", passive_deletes=True)
    # Add index on user_id for efficient querying
    Index('ix_user_id', user_id)


class InHourFrequency(str, Enum):
    Weekly = 'Weekly'
    Daily = 'Daily'
    EveryWeekDay = 'Every Weekday'
    WeekendsOnly = 'Weekends Only'
    EveryDayOfTheWeek = 'EveryDayOfTheWeek'


class InHours(Base, SoftDeleteMixin):
    __tablename__ = "consultant_in_hours"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.date.today())
    end_time = Column(DateTime, default=datetime.date.today())
    specialist_id = Column(Integer, ForeignKey("consultant_specialist.id"))
    frequency = Column(SqlEnum(InHourFrequency))
    service_id = Column(Integer, ForeignKey("service_listing.service_id"))

    # consultation_queue = relationship("ConsultationQueue", backref="consultant_in_hours")


class SpecialistSpecialization(Base, SoftDeleteMixin):
    __tablename__ = "consultant_specialist_specialization"
    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("consultant_specialist.id", ))
    specialism_id = Column(Integer, ForeignKey("consultant_department.id", ))

    # Indexes for optimized searching
    Index('ix_specialist_specialization', specialist_id, specialism_id)


class ConsultationQueue(Base, SoftDeleteMixin):
    __tablename__ = "consultation_queue"
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("consultant_in_hours.id", ondelete="cascade"))
    scheduled_at = Column(Date, default=datetime.date.today())
    status = Column(SqlEnum(QueueStatus), default=QueueStatus.Processing)
    booking_id = Column(Integer, ForeignKey("service_booking_detail.id", ondelete="cascade"))
    specialization_id = Column(Integer, ForeignKey("consultant_department.id", ondelete="cascade"))
    notes = Column(Text, nullable=True)
    consultation_time = Column(DateTime)

    # Relationship to Schedule
    # in_hours = relationship("InHours", backref="consultation_queue", lazy='select')
    consultations = relationship("Consultations", back_populates="queue", passive_deletes=True)

    # Index for faster queries
    Index('ix_schedule_status', schedule_id, status)


class ConsultationType(str, Enum):
    base_case = 'base_case'
    follow_up = 'follow_up'


class Consultations(Base, SoftDeleteMixin):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True, index=True)
    consultation_type = Column(SqlEnum(ConsultationType), default=ConsultationType.base_case)
    queue_id = Column(Integer, ForeignKey("consultation_queue.id"))
    reason_for_visit = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("consultant_specialist.id", ondelete="cascade"))
    preliminary_diagnosis = Column(String(250), nullable=True)
    # final_diagnosis = Column(String(250), nullable=True)

    queue = relationship("ConsultationQueue", back_populates="consultations", passive_deletes=True)
    creator = relationship("Specialist", back_populates="consultations", passive_deletes=True)


class ConsultationClinicalExamination(Base, SoftDeleteMixin):
    __tablename__ = "consultation_clinical_examination"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="cascade"))
    clinical_examination_id = Column(Integer, ForeignKey("clinical_examination.id", ondelete="cascade"))


class ConsultationPrescription(Base, SoftDeleteMixin):
    __tablename__ = "consultation_prescription"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="cascade"))
    prescription_id = Column(Integer, ForeignKey("pharmacy_prescription.id", ondelete="cascade"))


class ConsultationHierarchy(Base, SoftDeleteMixin):
    __tablename__ = "consultation_hierarchy"
    id = Column(Integer, primary_key=True, index=True)
    base_consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="cascade"))
    follow_up_consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="cascade"))


class InternalSystems(str, Enum):
    respiratory = 'respiratory'
    general = 'general'
    cardiovascular = 'cardiovascular'
    gastrointestinal = 'gastrointestinal'
    neurological = 'neurological'
    musculoskeletal = 'musculoskeletal'
    integumentary = 'integumentary'
    urinary = 'urinary'
    reproductive = 'reproductive'
    dermatological = 'dermatological'
    psychiatric = 'psychiatric'


class ConsultationRoS(Base, SoftDeleteMixin):
    __tablename__ = "consultation_review_of_system"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="cascade"))
    system = Column(SqlEnum(InternalSystems))
    note = Column(Text, nullable=True)

    # consultations = relationship("Consultations", backref="consultation_review_of_system", lazy='select')


class Symptom(Base, SoftDeleteMixin):
    __tablename__ = 'symptom'
    id = Column(Integer, primary_key=True, index=True)
    symptom = Column(String(150), index=True)


class PresentingSymptomsFrequency(str, Enum):
    Low = 'Low'
    Medium = 'Medium'
    High = 'High'


class SymptomFrequency(str, Enum):
    Weekly = 'Weekly'
    Hourly = 'Hourly'
    Monthly = 'Monthly'
    Daily = 'Daily'
    Annually = 'Annually'


class PresentingSymptom(Base, SoftDeleteMixin):
    __tablename__ = 'consultation_presenting_symptoms'
    id = Column(Integer, primary_key=True, index=True)
    clinical_examination_id = Column(Integer, ForeignKey("clinical_examination.id", ondelete="cascade"))
    symptom_id = Column(Integer, ForeignKey("symptom.id", ondelete="cascade"))
    severity = Column(SqlEnum(Severity))
    frequency = Column(SqlEnum(SymptomFrequency, name="symptom_frequency"))

    # Relationships
    symptom = relationship("Symptom", backref="presenting_symptoms", lazy='select')
    clinical_examination = relationship("ClinicalExamination", backref="presenting_symptoms", lazy='select')

    # Index('ix_symptom_frequency', symptom_id, frequency)


class ClinicalExamination(Base, SoftDeleteMixin):
    __tablename__ = 'clinical_examination'
    id = Column(Integer, primary_key=True, index=True)
    presenting_complaints = Column(Text)
    conducted_at = Column(Date, default=datetime.date.today())
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))
    conducted_by = Column(Integer, ForeignKey("users.id", ondelete="cascade"))

    # Relationships and indexes for fast access
    transaction = relationship("Transaction", backref="clinical_examinations", lazy='select')
    conducted_by_user = relationship("User", backref="clinical_examinations", lazy='select')

    # Index('ix_transaction_id', transaction_id)
    Index('ix_exam_conducted_by', conducted_by)


