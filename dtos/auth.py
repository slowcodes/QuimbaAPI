from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from dtos.people import PersonDTO
from models.auth import AccountStatus


class AccountDTO(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    username: str
    password: Optional[str] = None
    # confirm_password: Optional[str]
    created_at: Optional[str] = None
    status: Optional[AccountStatus] = AccountStatus.Active
    person_id: Optional[int] = None
    person: Optional[PersonDTO] = None
    #
    # class Config:
    #     orm_mode = True


class SignUpResponseDTO(BaseModel):
    error: Optional[bool] = None
    data: Optional[AccountDTO] = None
    msg: str


class PrivilegeDTO(BaseModel):
    id: Optional[int] = None
    can_execute: bool
    can_read: bool
    can_write: bool
    privilege_id: Optional[int]
    group_id: int


class AccountActivityDTO(BaseModel):
    id: Optional[int] = None
    last_modified: Optional[str]
    last_login: Optional[str]
    user_id: int


class UserDTO(AccountDTO):
    first_name: str
    last_name: str
    roles: Optional[List[int]] = None
    privileges: Optional[List[PrivilegeDTO]] = None
    # disabled: bool | None = None


class RoleDTA(BaseModel):
    id: Optional[int] = None
    role_name: str
    role_type: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserInDB(UserDTO):
    hashed_password: str


class UserGroupDTO(BaseModel):
    id: Optional[int] = None
    group_name: str
    group_desc: str
    privileges: Optional[List[PrivilegeDTO]]
    created_at: Optional[str] = None


class UserGroupMemberDTO(BaseModel):
    id: Optional[int] = None
    group_id: int
    user_id: int
    created_at: Optional[str] = None
