import datetime

from sqlalchemy import Boolean, Column, Double, DateTime, ForeignKey, Integer, String, Date, Enum as SqlEnum, Text, \
    Index, \
    BLOB, LargeBinary, CheckConstraint
from sqlalchemy.orm import relationship
from models.mixins import SoftDeleteMixin
from db import Base
from enum import Enum
from sqlalchemy.types import Enum as SQLEnum  # avoid collision

from sqlalchemy import Column, Integer, String, Text, DateTime, func


class MaritalStatus(str, Enum):
    Single = 'Single'
    Married = 'Married'
    Divorced = 'Divorced'
    Separated = 'Separated'
    Confidential = 'Prefer not to say'


class Sex(str, Enum):
    Male = 'Male'
    Female = 'Female'


class ProfTitle(str, Enum):
    Mr = 'Mr'
    Mrs = 'Mrs'
    Dr = 'Dr'
    Chief = 'Chief'
    Miss = 'Miss'
    Prof = 'Prof'
    Scientist = 'Scientist'
    Barr = 'Barr'


class Person(Base, SoftDeleteMixin):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(SqlEnum(ProfTitle), nullable=True)
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(30), nullable=False)
    middle_name = Column(String(30), nullable=True)
    sex = Column(SqlEnum(Sex), nullable=False)
    email = Column(String(50), nullable=True)
    phone = Column(String(11), nullable=True, index=True)  # Unique phone
    enrollment_date = Column(DateTime, default=datetime.datetime.utcnow)

    deleted_at = Column(DateTime, nullable=True)  # Soft delete field

    client = relationship("Client", back_populates="person", uselist=False, cascade="all, delete")
    person_type = relationship("PersonType", back_populates="person", cascade="all, delete")
    organization_people = relationship("OrganizationPeople", back_populates="person", cascade="all, delete")

    __table_args__ = (
        CheckConstraint("LENGTH(phone) <= 11", name="check_phone_length"),
        Index("idx_person_email", "email"),
        Index("idx_person_phone", "phone"),
        Index("idx_person_first_name", "first_name"),
        Index("idx_person_last_name", "last_name"),
    )

    def soft_delete(self, db_session):
        """Soft deletes a person by setting deleted_at timestamp."""
        self.deleted_at = datetime.datetime.utcnow()
        db_session.commit()


class TypeOfPerson(Enum):
    Client = 'Client'
    User = 'User'  # Staff
    Referral = 'Referral'


class PersonType(Base, SoftDeleteMixin):
    __tablename__ = "person_type"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="cascade"))
    person_type = Column(SqlEnum(TypeOfPerson), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    person = relationship("Person", back_populates="person_type")


class Client(Base, SoftDeleteMixin):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, index=True)
    photo = Column(LargeBinary)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="cascade"), unique=True)
    marital_status = Column(SqlEnum(MaritalStatus), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    referral_id = Column(Integer, ForeignKey("client_referral.id", ondelete="cascade"), nullable=True)
    blood_group = Column(String(3), nullable=True)
    address = Column(String(100), nullable=True)
    lga_id = Column(Integer, ForeignKey("lga.id", ondelete="cascade"), nullable=True)
    occupation_id = Column(Integer, ForeignKey("client_occupation.id", ondelete="cascade"), nullable=True)

    person = relationship("Person", back_populates="client")
    lga = relationship("Lga", back_populates="client")
    occupation = relationship("Occupation", back_populates="clients")
    lifestyles = relationship("ClientLifestyle", back_populates="patient")
    drug_allergies = relationship("DrugAllergy", back_populates="client", cascade="all, delete-orphan")
    food_allergies = relationship("FoodAllergy", back_populates="client", cascade="all, delete-orphan")
    service_carts = relationship("ClientServiceCart", back_populates="client")

    # referral = relationship("OrganizationPeople", back_populates="client")


class LifestyleCategory(Enum):
    personal_medical_history = "personal_medical_history"
    family_medical_history = "family_medical_history"
    obstetric_gynecologic_history = "obstetric_gynecologic_history"
    personal_habits = "personal_habits"
    diet = "diet"
    exercise = "exercise"
    sleep_pattern = "sleep_pattern"
    work_stress = "work_stress"
    sex_reproductive_health = "sex_reproductive_health"
    other_life_style = "other_life_style"


class LifestyleFactor(Base):
    __tablename__ = "client_lifestyle_factors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., "smoking", "alcohol"
    category = Column(SQLEnum(LifestyleCategory), nullable=True)  # now an enum
    value_type = Column(SQLEnum("string", "list", "int", "enum", "text", name="lifestyle_value_type"), nullable=False)
    allowed_values = Column(Text, nullable=True)  # JSON or CSV list for enums

    patient_values = relationship("ClientLifestyle", back_populates="factor")


class ClientLifestyle(Base):
    __tablename__ = "client_lifestyles"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)
    factor_id = Column(Integer, ForeignKey("client_lifestyle_factors.id"), nullable=False)

    value = Column(Text, nullable=True)  # stored as string, interpreted based on factor.value_type

    factor = relationship("LifestyleFactor", back_populates="patient_values")
    patient = relationship("Client", back_populates="lifestyles")


class OrganizationPeople(Base):
    __tablename__ = "organization_people"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="cascade"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="cascade"))
    deleted_at = Column(DateTime, nullable=True)  # Soft delete field

    # client = relationship("Client", back_populates="referral")
    person = relationship("Person", back_populates="organization_people")
    organization = relationship("Organization", back_populates="organization_people")
    client_referral = relationship("Referral", back_populates="organization_people", uselist=False,
                                   cascade="all, delete")
    __table_args__ = (
        CheckConstraint(
            "person_id IS NOT NULL OR organization_id IS NOT NULL",
            name="check_at_least_one_entity"
        ),
    )


class Icd10(Base):
    __tablename__ = "icd10_head_codes"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(200), nullable=True)
    head_code = Column(String(300), nullable=True)
    name = Column(String(300), nullable=True)



class State(Base):
    __tablename__ = "state"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(30), unique=True, index=True, nullable=False)

    lga = relationship("Lga", back_populates="state")


class Lga(Base):
    __tablename__ = "lga"

    id = Column(Integer, primary_key=True, index=True)
    lga = Column(String(25), nullable=False)
    state_id = Column(Integer, ForeignKey("state.id", ondelete="cascade"))

    state = relationship("State", back_populates="lga")
    client = relationship("Client", back_populates="lga")
    organization = relationship("Organization", back_populates="lga")


class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    phone = Column(String(11), nullable=False)
    address = Column(String(50), nullable=True)
    lga_id = Column(Integer, ForeignKey("lga.id", ondelete="cascade"))
    deleted_at = Column(DateTime, nullable=True)  # Soft delete field

    lga = relationship("Lga", back_populates="organization")
    organization_people = relationship("OrganizationPeople", back_populates="organization",
                                       cascade="all, delete")


class Occupation(Base):
    __tablename__ = "client_occupation"

    id = Column(Integer, primary_key=True, index=True)
    occupation = Column(String(50), nullable=False)

    clients = relationship("Client", back_populates="occupation")


class Severity(str, Enum):
    Low = 'Low'
    Medium = 'Medium'
    High = 'High'


class DrugAllergy(Base):
    __tablename__ = 'client_drug_allergy'

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("pharmacy_drug.id", ))
    detail = Column(String(100))
    risk_severity = Column(SqlEnum(Severity))
    client_id = Column(Integer, ForeignKey("client.id", ))

    drug = relationship("Drug", back_populates="allergies")
    client = relationship("Client", back_populates="drug_allergies")


class FoodAllergy(Base):
    __tablename__ = 'client_food_allergy'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    food = Column(String(100))
    detail = Column(String(100))
    risk_severity = Column(SqlEnum(Severity))

    client = relationship("Client", back_populates="food_allergies")


class VitalType(str, Enum):
    BMI = 'BMI'
    BloodGlucose = 'Blood Glucose'
    BloodPressure = 'Blood Pressure'
    Weight = 'Weight',
    Tempreture = 'Temperature'


class Vitals(Base):
    __tablename__ = "client_vital"
    id = Column(Integer, primary_key=True, index=True)
    vital_type = Column(SqlEnum(VitalType))
    vital_value = Column(String(15))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))


class PrivacyType(str, Enum):
    Complete = 'Complete_Anonymity'
    Basic = 'Basic_Anonymity'
    Marketing_Comm = 'Marketing_Comm'


class Privacy(Base):
    __tablename__ = "client_privacy"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    is_age_privacy = Column(Boolean, default=False)
    is_sex_privacy = Column(Boolean, default=False)
    is_name_privacy = Column(Boolean, default=False)
    is_others_privacy = Column(Boolean, default=False)


class ClientNotification(Base):
    """
    Represents a client notification template with default messages
    for SMS, WhatsApp, and email.
    """
    __tablename__ = "client_notification"  # Use lowercase snake_case for table name

    id = Column(Integer, primary_key=True)  # Primary keys are automatically indexed
    notification = Column(String(100), nullable=False, doc="Title or description of the notification")
    default_sms_msg = Column(Text, doc="Default message template for SMS")
    default_whatsapp_msg = Column(Text, doc="Default message template for WhatsApp")
    default_email_msg = Column(Text, doc="Default message template for Email")
    created_at = Column(DateTime, default=func.now(), doc="Timestamp of when the record was created")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), doc="Timestamp of the last update")

    # class Config:
    #     orm_mode = True

    def to_dict(self):
        """
        Converts the object to a dictionary for serialization.
        """
        return {
            "id": self.id,
            "notification": self.notification,
            "default_sms_msg": self.default_sms_msg,
            "default_whatsapp_msg": self.default_whatsapp_msg,
            "default_email_msg": self.default_email_msg,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class MsgType(str, Enum):
    SMS = 'SMS'
    Email = 'Email'
    WhatsApp = 'WhatsApp'


class ClientNotificationSubscription(Base):
    __tablename__ = "client_notification_subscription"
    id = Column(Integer, primary_key=True, index=True)
    msg_type = Column(SqlEnum(MsgType))
    client_id = Column(Integer, ForeignKey("client.id", ondelete="cascade"))
    created_at = Column(DateTime, default=func.now(), doc="Timestamp of when the record was created")
    notification_id = Column(Integer, ForeignKey("client_notification.id", ondelete="cascade"))


class Referral(Base):
    __tablename__ = "client_referral"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), doc="Timestamp of when the record was created")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), doc="Timestamp of last update")
    deleted_at = Column(DateTime, nullable=True, doc="Timestamp of soft deletion")
    org_people_id = Column(Integer, ForeignKey("organization_people.id", ondelete="cascade"), nullable=True)

    organization_people = relationship("OrganizationPeople", back_populates="client_referral")
    client_service_carts = relationship("ClientServiceCart", back_populates="client_referral")