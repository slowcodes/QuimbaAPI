from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
import datetime

from sqlalchemy.orm import relationship

from db import Base
from models.mixins import SoftDeleteMixin


class Notification(Base, SoftDeleteMixin):
    __tablename__ = 'user_notification'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
