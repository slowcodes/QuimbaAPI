from typing import Annotated, List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.responses import JSONResponse

from dtos.auth import Token, UserDTO, UserGroupDTO, UserGroupMemberDTO, AccountDTO, SignUpResponseDTO
from repos.auth_repository import UserRepository
from db import get_db
from sqlalchemy.orm import Session

from repos.client.person_repository import PersonRepository
from security.config import ACCESS_TOKEN_EXPIRE_MINUTES
from security.dependencies import get_current_active_user, create_access_token, require_role_and_privilege

security_router = APIRouter(prefix="/api/v1/auth", tags=["Security"])


# security_router = APIRouter(tags=["Security"])


def auth_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_person_repository(db: Session = Depends(get_db)) -> PersonRepository:
    return PersonRepository(db)


@security_router.post("/login")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        repo: UserRepository = Depends(auth_repo)) -> Token:
    user = repo.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@security_router.put("/signup", response_model=SignUpResponseDTO, status_code=status.HTTP_202_ACCEPTED)
async def sign_up(signup_dto: AccountDTO,
                  auth=Depends(auth_repo),
                  # person_repo=Depends(get_person_repository),
                  security=Depends(require_role_and_privilege(20, "write"))
                  ):
    updated_user = auth.updateSignUp(signup_dto)
    if updated_user.error:
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            content=dict(error=True, msg='User does not exist'))
    return updated_user


@security_router.post("/signup", response_model=SignUpResponseDTO, status_code=status.HTTP_201_CREATED)
async def sign_up(signup_dto: AccountDTO,
                  auth=Depends(auth_repo),
                  person_repo=Depends(get_person_repository),
                  security=Depends(require_role_and_privilege(20, "write"))
                  ):
    if person_repo.person_exists(signup_dto.person):
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            content=dict(error=True, msg='A similar entry already exist'))
    new_user = auth.register_user(signup_dto)
    return SignUpResponseDTO(error=False, data=new_user, msg='User registered successfully')


@security_router.get("/users/me/", response_model=UserDTO)
async def read_users_me(
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
    return current_user


@security_router.get("/users")
async def get_all_user(skip: int = 0, limit: int = 20, auth=Depends(auth_repo),
                       security=Depends(require_role_and_privilege(20, "read"))
                       ):
    return auth.get_all_users(limit, skip)


@security_router.get("/users/{id}")
async def getUserById(id: int,
                      auth=Depends(auth_repo),
                      person_repo=Depends(get_person_repository),
                      security=Depends(require_role_and_privilege(20, "read"))):
    usr_details = auth.get_user_by_id(id)
    person = person_repo.get(usr_details.person_id)
    return {
        'id': person.id,
        'first_name': person.first_name,
        'last_name': person.last_name,
        'middle_name': person.middle_name,
        'email': person.email,
        'phone': person.phone,
        'sex': person.sex,
        'title': person.title,
        # 'date_of_birth': person.date_of_birth,
        'user_account': usr_details
    }


@security_router.put("/users/update-user")
async def update_user_account(account_dto: AccountDTO, auth=Depends(auth_repo),
                              security=Depends(require_role_and_privilege(20, "execute"))
                              ):
    return auth.update_user(account_dto)


@security_router.get("/users/password_reset")
async def reset_user_password(password: str,
                              new_password: str,
                              new_password_confirm: str,
                              username: str, auth=Depends(auth_repo),
                              security=Depends(require_role_and_privilege(20, "execute"))
                              ):
    is_reset = auth.reset_password(password, new_password, new_password_confirm, username)
    if is_reset:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=dict(error=False, msg='Lab added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        content=dict(error=False, msg='unable to reset password. A similar entry already exist'))


@security_router.get("/users/roles")
async def get_roles(
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
        auth=Depends(auth_repo)):
    return auth.get_all_roles()


@security_router.get("/users/group/")  # response_model=List[UserGroupDTO]
async def get_groups(
        auth=Depends(auth_repo),
        security=Depends(require_role_and_privilege(20, "read"))
):
    return auth.get_all_groups()
    # JSONResponse(
    #     status_code=status.HTTP_200_OK,
    #     content=(auth.get_all_groups())
    # )


@security_router.post("/users/group")
def add_group(group: UserGroupDTO,
              auth=Depends(auth_repo),
              security=Depends(require_role_and_privilege(20, "write"))
              ):
    return auth.add_user_group(group)


@security_router.post("/users/group/member")
def add_group_member(member: UserGroupMemberDTO,
                     auth=Depends(auth_repo),
                     security=Depends(require_role_and_privilege(20, "write"))
                     ):
    return auth.add_user_to_group(member)


@security_router.delete("/users/group/member")
def remove_group_member(user_id: int, group_id: int,
                        auth=Depends(auth_repo),
                        security=Depends(require_role_and_privilege(20, "execute"))
                        ):
    return auth.remove_user_from_group(user_id, group_id)


@security_router.get("/users/group/member/")
def get_all_user_group_members(user_id: int,
                               auth=Depends(auth_repo),
                               security=Depends(require_role_and_privilege(20, "read"))
                               ):
    return auth.get_all_user_groups(user_id)
