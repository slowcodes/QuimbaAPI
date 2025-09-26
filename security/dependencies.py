from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from dtos.auth import UserDTO, TokenData, PrivilegeDTO
from db import get_db
from models.auth import AccountStatus
from repos.auth_repository import UserRepository
from security.config import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def auth_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           repo: UserRepository = Depends(auth_repo)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = repo.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[UserDTO, Depends(get_current_user)],
):
    if current_user.status != AccountStatus.Active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: str):
    def role_checker(current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
        if required_role not in current_user.roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user

    return role_checker


def find_privilege_by_id(privileges: list[PrivilegeDTO], x: int) -> PrivilegeDTO | None:
    return next((p for p in privileges if p.id == x), None)


def require_access_privilege(privilege: int):
    def privilege_checker(current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
        if find_privilege_by_id(current_user.privileges, privilege) is None:
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return current_user

    return privilege_checker


def require_role_and_privilege(privilege_id: int, permission: str):
    def role_and_privilege_checker(current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
        print('current user', current_user.roles, current_user.privileges)
        if not has_permission(current_user.privileges, privilege_id, permission):
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return current_user

    return role_and_privilege_checker


def has_permission(privileges: list, privilege_id: int, permission: str) -> bool:
    for privilege in privileges:
        if privilege.privilege_id == privilege_id:
            if permission == "read":
                return privilege.can_read
            elif permission == "write":
                return privilege.can_write
            elif permission == "execute":
                return privilege.can_execute
    return False  # No matching privilege or invalid permission
