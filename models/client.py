import datetime

from sqlalchemy import Boolean, Column, Double, DateTime, ForeignKey, Integer, String, Date, Enum as SqlEnum, Text, BLOB
from db import Base
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, func


class MaritalStatus(str, Enum):
    Single = 'Single'
    SINGLE = 'SINGLE'
    Married = 'Married'
    Divorced = 'Divorced'
    Separated = 'Separated'
    Confidential = 'Prefer not to say'


class Sex(str, Enum):
    Male = 'Male'
    Female = 'Female'


class Person(Base):
    __tablename__ = "Person"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(30))
    last_name = Column(String(30))
    middle_name = Column(String(30))
    sex = Column(SqlEnum(Sex))
    email = Column(String(50), unique=True)
    phone = Column(String(25))  # Made 25 due to faker generator. should be 11
    enrollment_date = Column(Date, default=datetime.date.today())


class Client(Base):
    __tablename__ = "Client"

    id = Column(Integer, primary_key=True, index=True)
    photo = Column(BLOB)
    person_id = Column(Integer, ForeignKey("Person.id", ondelete="CASCADE"))
    marital_status = Column(SqlEnum(MaritalStatus))
    date_of_birth = Column(Date)
    blood_group = Column(String(3))
    address = Column(String(100))
    lga_id = Column(Integer, ForeignKey("Lga.id", ondelete='CASCADE'))
    occupation_id = Column(Integer, ForeignKey("Client_Occupation.id", ondelete='CASCADE'))


class OrganizationPeople(Base):
    __tablename__ = "Client_Organisation"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    organization_id = Column(Integer, ForeignKey("Client_Organization.id", ondelete='CASCADE'))


class State(Base):
    __tablename__ = "Client_State"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(30), unique=True, index=True)


class Lga(Base):
    __tablename__ = "Lga"

    id = Column(Integer, primary_key=True, index=True)
    lga = Column(String(25))
    state_id = Column(Integer, ForeignKey("State.id", ondelete='CASCADE'))


class Organization(Base):
    __tablename__ = "Client_Organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20))
    email = Column(String(50))
    phone = Column(String(11))
    address = Column(String(50))
    lga_id = Column(Integer, ForeignKey("Lga.id", ondelete='CASCADE'))


class Occupation(Base):
    __tablename__ = "Client_Occupation"
    id = Column(Integer, primary_key=True, index=True)
    occupation = Column(Text)


class Severity(str, Enum):
    Low = 'Low'
    Medium = 'Medium'
    High = 'High'


class DrugAllergy(Base):
    __tablename__ = 'Client_Drug_Allergy'

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer)  # Column(Integer, ForeignKey("Pharmacy_Drug.id", ondelete='CASCADE'))
    detail = Column(String(100))
    risk_severity = Column(SqlEnum(Severity))
    client_id = Column(Integer)  # Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))


class FoodAllergy(Base):
    __tablename__ = 'Client_Food_Allergy'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    food = Column(String(100))
    detail = Column(String(100))
    risk_severity = Column(SqlEnum(Severity))


class VitalType(str, Enum):
    BMI = 'BMI'
    BloodGlucose = 'Blood Glucose'
    BloodPressure = 'Blood Pressure'
    Weight = 'Weight',
    Tempreture = 'Temperature'


class Vitals(Base):
    __tablename__ = "Client_Vital"
    id = Column(Integer, primary_key=True, index=True)
    vital_type = Column(SqlEnum(VitalType))
    vital_value = Column(String(15))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))


class PrivacyType(str, Enum):
    Complete = 'Complete_Anonymity'
    Basic = 'Basic_Anonymity'
    Marketing_Comm = 'Marketing_Comm'


class Privacy(Base):
    __tablename__ = "Client_Privacy"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    is_age_privacy = Column(Boolean, default=False)
    is_sex_privacy = Column(Boolean, default=False)
    is_name_privacy = Column(Boolean, default=False)
    is_others_privacy = Column(Boolean, default=False)


class ClientNotification(Base):
    """
    Represents a client notification template with default messages
    for SMS, WhatsApp, and email.
    """
    __tablename__ = "Client_Notification"  # Use lowercase snake_case for table name

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
    __tablename__ = "Client_Notification_Subscription"
    id = Column(Integer, primary_key=True, index=True)
    msg_type = Column(SqlEnum(MsgType))
    client_id = Column(Integer, ForeignKey("Client.id", ondelete='CASCADE'))
    created_at = Column(DateTime, default=func.now(), doc="Timestamp of when the record was created")
    notification_id = Column(Integer, ForeignKey("Client_Notification.id", ondelete='CASCADE'))
