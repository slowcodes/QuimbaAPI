from operator import and_
from typing import Annotated, List
from sqlalchemy import or_

from sqlalchemy.orm import Session

from commands.auth import UserDTO, UserInDB, TokenData, RoleDTA, UserGroupDTO, PrivilegeDTO, UserGroupMemberDTO, \
    AccountDTO
from models.auth import User, AccountStatus, Roles, PrivilegeListing, UserGroup, UserGroupPrivilege, UserGroupMember
from models.client import Person
from security.utils import verify_password, get_password_hash, is_bcrypt_hash


class UserRepository:
    def __init__(self, session: Session):
        self.session = session
        self.cols = [
            User.id,
            User.username,
            Person.first_name,
            Person.last_name,
            Person.email,
            User.status,
            User.created_at,
            User.password,
            User.person_id
        ]

        self.SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        self.ALGORITHM = "HS256"
        # The commented columns caused issued. Suspects column types in the model
        # User.created_at,
        # User.last_modified,
        # User.last_login
        self.query = self.session.query(*self.cols).select_from(User). \
            join(Person, Person.id == User.person_id)

    def create_user(self, user_data: dict):
        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        return user

    def get_user_by_id(self, user_id: int) -> User | None:

        user = self.query.filter(User.id == user_id).one_or_none()

        if user is None:
            return None

        # return user
        return User(
                id=user.id,
                username=user.username,
                person_id=user.person_id,
                password=user.password,
                status=user.status,
                # created_at=user.created_at
        )

    def get_user(self, username: str):

        user = self.query.filter(or_(User.username == username, Person.email == username)).first()
        user_dict = None
        if user:
            user_dict = UserDTO(
                id=user.id,
                username=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                status=AccountStatus.Active,
                person_id=user.person_id,
                password=user.password,
                roles=[],
                privileges=[25, 45]
            )

        return user_dict
        # return None

    def update_user(self, account_dto: AccountDTO):
        # self.create_user(
        #     {
        #         "username": "nd_ekekwe",
        #         "password": "$2b$12$gtRoj575/uH.iufajh2OSOajlIB0alq7IYwVrnXzhR7J8E2Oax/hC",
        #         "status": AccountStatus.Active,
        #         "person_id": 5
        #     }
        # )
        # user = self.query.filter(User.id == account_dto.id).one_or_none()
        user = self.session.query(User)\
            .filter(User.status != AccountStatus.Deleted)\
            .filter(User.id == account_dto.id).first()

        if user is None:
            return None

        account_data = account_dto.dict(exclude_unset=True)
        for key, value in account_data.items():

            if key == 'password':
                # If the password is not a hash, hash it
                value = get_password_hash(value) if not is_bcrypt_hash(value) else value
            if key not in {'created_at'}:
                setattr(user, key, value)
        self.session.commit()
        self.session.refresh(user)

                # try:
                #     print(f"Setting {key} to {value}")
                #     setattr(user, key, value)
                #     self.session.commit(user)
                # except AttributeError as e:
                #     print(f"Failed to set attribute {key}: {e}")
        # user.username = account_dto.username
        # user_account.person_id = account_dto.person_id

        # $2b$12$gtRoj575/uH.iufajh2OSOajlIB0alq7IYwVrnXzhR7J8E2Oax/hC nd_ekekwe, person_id:5, status: Active

        return {
            'username': user.username
        }

    def get_all_users(self, limit: int = 20, skip: int = 0):
        users_query = self.query.filter(User.status != AccountStatus.Deleted).offset(skip).limit(limit).all()
        users = []
        for user in users_query:
            users.append(
                {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'status': user.status,
                    'created_at': user.created_at
                }
            )
        return {
            'data': users,
            'total': self.query.count()
        }

    def authenticate_user(self, usr: str, password: str):
        user = self.get_user(usr)

        if not user:
            return False
        if not verify_password(password, user.password):
            return False

        return user

    def reset_password(self) -> bool:
        return True

    def get_role_privileges_by_role_id(self, role_id):
        return self.session.query(PrivilegeListing).filter(PrivilegeListing.role_id == role_id).all()

    def get_all_roles(self):
        roles = self.session.query(Roles).all()

        roles_and_privileges = []
        for role in roles:
            roles_and_privileges.append({
                'id': role.id,
                'role_name': role.role_name,
                'role_type': role.role_type,
                'privileges': self.get_role_privileges_by_role_id(role.id)
            })
        return roles_and_privileges

    def add_user_group(self, group: UserGroupDTO):
        user_group = UserGroup(
            group_name=group.group_name,
            group_desc=group.group_desc
        )
        self.session.add(user_group)
        self.session.commit()
        self.session.refresh(user_group)
        self.add_group_privilege(group.privileges, user_group.id)

        return user_group

    def add_group_privilege(self, privileges: List[PrivilegeDTO], group_id: int):
        all_privileges = []
        for privilege in privileges:
            new_privilege = UserGroupPrivilege(
                group_id=group_id,
                privilege_id=privilege.privilege_id,
                can_read=privilege.can_read,
                can_write=privilege.can_write,
                can_execute=privilege.can_execute
            )
            self.session.add(
                new_privilege
            )
            self.session.commit()
            self.session.refresh(new_privilege)
            all_privileges.append(
                new_privilege.__dict__
            )
        return all_privileges

    def get_privilege_by_group_id(self, group_id: int):
        cols = [
            UserGroupPrivilege.id,
            PrivilegeListing.privilege,
            UserGroupPrivilege.group_id,
            UserGroupPrivilege.privilege_id,
            Roles.role_name,
            UserGroupPrivilege.can_write,
            UserGroupPrivilege.can_read,
            UserGroupPrivilege.can_execute,
        ]
        # return self.session.query(UserGroupPrivilege).filter(UserGroupPrivilege.group_id == group_id).all()
        privileges = self.session.query(*cols).select_from(UserGroupPrivilege) \
            .join(PrivilegeListing, PrivilegeListing.id == UserGroupPrivilege.privilege_id) \
            .join(Roles, Roles.id == PrivilegeListing.role_id) \
            .filter(UserGroupPrivilege.group_id == group_id).all()

        response = []
        for privilege in privileges:
            response.append({
                'id': privilege.id,
                'privilege': privilege.privilege,
                'role': privilege.role_name,
                'can_write': privilege.can_write,
                'can_read': privilege.can_read,
                'can_execute': privilege.can_execute,
                'group_id': privilege.group_id,
            })
        return response

    def add_user_to_group(self, group_member: UserGroupMemberDTO):
        group_membership = UserGroupMember(
            user_id=group_member.user_id,
            group_id=group_member.group_id

        )
        self.session.add(group_membership)
        self.session.commit()
        self.session.refresh(group_membership)
        return group_membership

    def remove_user_from_group(self, user_id: int, group_id: int):
        members = self.session.query(UserGroupMember) \
            .filter(and_(UserGroupMember.group_id == group_id, UserGroupMember.user_id == user_id)).all()
        for member in members:
            self.session.delete(member)
        self.session.commit()
        return True

    def get_all_groups(self, skip: int = 0, limit: int = 20) -> List[UserGroup]:
        groups = self.session.query(UserGroup)
        group_count = groups.count()
        group_page = groups.offset(skip).limit(limit).all()

        groups_with_privileges = []
        for group in group_page:
            groups_with_privileges.append({
                'id': group.id,
                'group_name': group.group_name,
                'group_desc': group.group_desc,
                'created_at': group.created_at,
                'privileges': self.get_privilege_by_group_id(group.id)
            })

        return {
            'data': groups_with_privileges,
            'total': group_count
        }

    def get_all_user_groups(self, user_id: int):
        members = self.session.query(UserGroupMember) \
            .filter(UserGroupMember.user_id == user_id).all()

        my_groups = []
        for member in members:
            my_groups.append(member)
        return my_groups
