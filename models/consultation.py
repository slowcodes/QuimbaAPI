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

    # Relationships
    specialist_specializations = relationship("SpecialistSpecialization", back_populates="specialism", lazy='select')


class Specialist(Base, SoftDeleteMixin):
    __tablename__ = "consultant_specialist"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    title = Column(String(50))

    # Relationships
    specializations = relationship("SpecialistSpecialization", backref="specialist", lazy='select')
    consultant = relationship("Consultations", back_populates="creator", passive_deletes=True)
    prescriptions = relationship("Prescription", back_populates="consultant", lazy='select')
    user = relationship("User", back_populates="consultant_specialist", lazy='select')
    in_hours = relationship("InHours", back_populates="consultant", lazy='select')
    client_consultation_booking_carts = relationship(
        "ClientConsultationBookingCart",
        back_populates="consultant",
        lazy="select"
    )
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
    consultant = relationship("Specialist", back_populates="in_hours", lazy='select')
    business_service = relationship("BusinessServices", back_populates="in_hours", lazy='select')
    client_consultation_booking_carts = relationship(
        "ClientConsultationBookingCart",
        back_populates="schedule",
        lazy="select"
    )


class SpecialistSpecialization(Base, SoftDeleteMixin):
    __tablename__ = "consultant_specialist_specialization"
    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("consultant_specialist.id", ))
    specialism_id = Column(Integer, ForeignKey("consultant_department.id", ))

    specialism = relationship("Specialism", back_populates="specialist_specializations", lazy='select')

    # Indexes for optimized searching
    Index('ix_specialist_specialization', specialist_id, specialism_id)
    client_consultation_booking_carts = relationship(
        "ClientConsultationBookingCart",
        back_populates="specialization",
        lazy="select"
    )


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
    booking_detail = relationship("ServiceBookingDetail", back_populates="consultation_queue", lazy='select')

    # Index for faster queries
    Index('ix_schedule_status', schedule_id, status)


class ConsultationType(str, Enum):
    base_case = 'base_case'
    follow_up = 'follow_up'


class CaseStatus(str, Enum):
    Open = 'Open'
    Closed = 'Closed'
    Referred = 'Referred'
    Resolved = 'Resolved'


class Consultations(Base, SoftDeleteMixin):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    consultation_type = Column(SqlEnum(ConsultationType), default=ConsultationType.base_case)
    queue_id = Column(Integer, ForeignKey("consultation_queue.id"), unique=True)  # One-to-one relationship
    reason_for_visit = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("consultant_specialist.id", ondelete="cascade"))
    preliminary_diagnosis = Column(String(250), nullable=True)
    case_status = Column(SqlEnum(CaseStatus), default=CaseStatus.Open)

    queue = relationship("ConsultationQueue", back_populates="consultations", passive_deletes=True)
    creator = relationship("Specialist", back_populates="consultant", passive_deletes=True)

    consultation_clinical_examinations = relationship(
        "ConsultationClinicalExamination",
        back_populates="consultation",
        lazy="select"
    )
    # consultation_prescriptions = relationship("ConsultationPrescription", backref="consultation", lazy='select')
    review_of_systems = relationship("ConsultationRoS", back_populates="consultation", lazy='select')


class ConsultationClinicalExamination(Base, SoftDeleteMixin):
    __tablename__ = "consultation_clinical_examination"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="cascade"))
    clinical_examination_id = Column(Integer, ForeignKey("clinical_examination.id", ondelete="cascade"))

    consultation = relationship(
        "Consultations",
        back_populates="consultation_clinical_examinations",
        lazy="select"
    )

    clinical_examination = relationship(
        "ClinicalExamination",
        back_populates="consultation_clinical_examinations",
        lazy='select'
    )


class ConsultationPrescription(Base, SoftDeleteMixin):
    __tablename__ = "consultation_prescription"

    id = Column(Integer, primary_key=True, index=True)
    consultation_cart_id = Column(Integer, ForeignKey("client_service_cart.id", ondelete="cascade"))
    prescription_id = Column(Integer, ForeignKey("pharmacy_prescription.id", ondelete="cascade"))

    pharmacy_prescription = relationship("Prescription", back_populates="consultation_prescriptions", lazy='select')
    client_service_cart = relationship("ClientServiceCart", back_populates="prescription", lazy='select')


class ConsultationHierarchy(Base):
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

    consultation = relationship("Consultations", back_populates="review_of_systems", lazy='select')


class Symptom(Base, SoftDeleteMixin):
    __tablename__ = 'symptom'
    id = Column(Integer, primary_key=True, index=True)
    symptom = Column(String(150), index=True)

    # relationships
    presenting_symptoms = relationship("PresentingSymptom", back_populates="symptom", lazy='select')


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
    agreviating_factors = Column(Text, nullable=True)

    # Relationships
    symptom = relationship("Symptom", back_populates="presenting_symptoms", lazy='select')
    clinical_examination = relationship("ClinicalExamination", back_populates="symptoms", lazy='select')

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
    consultation_clinical_examinations = relationship(
        "ConsultationClinicalExamination",
        back_populates="clinical_examination",
        lazy="select"
    )

    symptoms = relationship("PresentingSymptom", back_populates="clinical_examination", lazy='select')
    # Index('ix_transaction_id', transaction_id)
    Index('ix_exam_conducted_by', conducted_by)
