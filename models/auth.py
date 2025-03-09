
from sqlalchemy import Column, ForeignKey, Integer, Boolean, String, DateTime, Enum as SqlEnum, func
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
    __tablename__ = 'User_Auth_Logs'
    id = Column(Integer, primary_key=True, index=True)
    log_date = Column(DateTime, default=datetime.datetime.utcnow)
    activity = Column(SqlEnum(AuthActivity), default=AuthActivity.Login)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"))


class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, nullable=False)
    password = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(SqlEnum(AccountStatus), default=AccountStatus.Active)
    person_id = Column(Integer, ForeignKey("Person.id"))
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
    __tablename__ = 'User_Role'
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(30))  # e.g Laboratory
    role_type = (Column(SqlEnum(ModuleType), default=ModuleType.Static))


class PrivilegeListing(Base):
    __tablename__ = 'User_Privilege_Listing'
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("User_Role.id", ondelete="CASCADE"))
    privilege = Column(String(50))  # e.g Sample Collection
    description = Column(String(200))


class UserGroup(Base):
    __tablename__ = 'User_Group'
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(30))
    group_desc = Column(String(50))
    created_at = Column(DateTime, default=datetime.date.today())


class UserGroupMember(Base):
    __tablename__ = 'User_Group_Member'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"))  # should be group.
    group_id = Column(Integer, ForeignKey("User_Group.id"), onupdate="CASCADE")
    member_since = Column(DateTime, default=datetime.datetime.utcnow)


class UserGroupPrivilege(Base):
    __tablename__ = 'User_Group_Privilege'
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("User_Group.id", ondelete="CASCADE"))  # should be group.
    privilege_id = Column(Integer, ForeignKey("User_Privilege_Listing.id", ondelete="CASCADE"))
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
    can_execute = Column(Boolean, default=False)
