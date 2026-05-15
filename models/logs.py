import datetime
from enum import Enum

from sqlalchemy import BigInteger, Integer, Column, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLEnum  #

from db import Base
from models.mixins import SoftDeleteMixin


class MessageType(Enum):
    Result = 'Result'
    Enrollment = 'Enrollment'
    Appointment = 'Appointment'
    Reminder = 'Reminder'


class Channel(Enum):
    Email = 'Email'
    WhatsApp = 'WhatsApp'
    SMS = 'SMS'


class LogType(Enum):
    Notification = 'Notification'


class Status(Enum):
    Success = 'Success'
    Failure = 'Failure'
    Pending = 'Pending'


class NotificationLog(Base, SoftDeleteMixin):
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(SQLEnum(Status, name="notification_log_status"), default=Status.Pending)
    message_type = Column(SQLEnum(MessageType, name="notification_message_type"), nullable=False)
    channel = Column(SQLEnum(Channel, name="notification_channel"), nullable=False)
    log_type = Column(SQLEnum(LogType, name="notification_log_type"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    transaction_id = Column(BigInteger, ForeignKey('transaction.id'), nullable=False)

    transaction = relationship("Transaction")
