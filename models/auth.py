
from sqlalchemy import Column, ForeignKey, Integer, Boolean, String, DateTime, Enum as SqlEnum, func
from sqlalchemy.orm import relationship

from db import Base
from enum import Enum

import datetime


class AccountStatus(str, Enum):
    Active = 'Active'
    Suspended = 'Suspended'
    Deleted = 'Deleted'
    Inactive = 'Inactive'


class AuthActivity(str, Enum):
    Modification = 'Modification'
    Login = 'Login'


class AuthLogs(Base):
    __tablename__ = 'user_auth_Logs'
    id = Column(Integer, primary_key=True, index=True)
    log_date = Column(DateTime, default=datetime.datetime.utcnow)
    activity = Column(SqlEnum(AuthActivity), default=AuthActivity.Login)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="cascade"))

    user = relationship("User", back_populates="auth_logs")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, nullable=False)
    password = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(SqlEnum(AccountStatus), default=AccountStatus.Active)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="cascade"))

    auth_logs = relationship("AuthLogs", back_populates="user")
    client_service_cart = relationship("ClientServiceCart", back_populates="user")
    #
    # @property
    # def status(self):
    #     return self._status
    #
    # @status.setter
    # def status(self, value):
    #     self._status = value

# class User(Base):
#     __tablename__ = 'Users'
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(30))
#     password = Column(String(200))
#     created_at = Column(DateTime, default=func.now())  # Generates timestamp at insertion time
#     last_modified = Column(DateTime, default=func.now(), onupdate=func.now())  # Updates timestamp on modification
#     last_login = Column(DateTime, default=func.now())
#     status = Column(SqlEnum(AccountStatus), default=AccountStatus.Active)
#     person_id = Column(Integer, ForeignKey("Person.id"))

class ModuleType(str, Enum):
    Dynamic = 'Dynamic'
    Static = 'Static'


class Roles(Base):  # Roles represents modules
    __tablename__ = 'user_role'
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(30))  # e.g Laboratory
    role_type = (Column(SqlEnum(ModuleType), default=ModuleType.Static))


class PrivilegeListing(Base):
    __tablename__ = 'user_privilege_listing'
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("user_role.id", ondelete="cascade"))
    privilege = Column(String(50))  # e.g Sample Collection
    description = Column(String(200))


class UserGroup(Base):
    __tablename__ = 'user_group'
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(30))
    group_desc = Column(String(50))
    created_at = Column(DateTime, default=datetime.date.today())


class UserGroupMember(Base):
    __tablename__ = 'user_group_member'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="cascade"))  # should be group.
    group_id = Column(Integer, ForeignKey("user_group.id", ondelete="cascade"))
    member_since = Column(DateTime, default=datetime.datetime.utcnow)


class UserGroupPrivilege(Base):
    __tablename__ = 'user_group_privilege'
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("user_group.id", ondelete="cascade"))  # should be group.
    privilege_id = Column(Integer, ForeignKey("user_privilege_listing.id", ondelete="cascade"))
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
    can_execute = Column(Boolean, default=False)
