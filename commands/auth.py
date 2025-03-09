from datetime import datetime, date
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field
from models.auth import AccountStatus


class AccountDTO(BaseModel):
    id: Optional[int]
    username: str
    password: Optional[str]
    created_at: Optional[str]
    status: Optional[AccountStatus]
    person_id: Optional[int]
    #
    # class Config:
    #     orm_mode = True


class AccountActivityDTO(BaseModel):
    id: Optional[int]
    last_modified: Optional[str]
    last_login: Optional[str]
    user_id: int


class UserDTO(AccountDTO):
    first_name: str
    last_name: str
    roles: Optional[List[int]]
    privileges: Optional[List[int]]
    # disabled: bool | None = None


class RoleDTA(BaseModel):
    id: Optional[int]
    role_name: str
    role_type: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserInDB(UserDTO):
    hashed_password: str


class PrivilegeDTO(BaseModel):
    id: Optional[int]
    can_execute: bool
    can_read: bool
    can_write: bool
    privilege_id: int
    group_id: int


class UserGroupDTO(BaseModel):
    id: Optional[int]
    group_name: str
    group_desc: str
    privileges: Optional[List[PrivilegeDTO]]
    created_at: Optional[str]


class UserGroupMemberDTO(BaseModel):
    id: Optional[int]
    group_id: int
    user_id: int
    created_at: Optional[str]
