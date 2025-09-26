from pathlib import Path
from typing import Optional

import csv

from sqlalchemy import String, cast, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from dtos.people import ClientDTO, OrganisationDTO, LocalityDTO, OccupationDTO
from models.auth import AccountStatus, User
from models.client import Client, Occupation, Lga, State, OrganizationPeople, Organization, Person
import logging
from datetime import datetime

from repos.auth_repository import UserRepository
from repos.client.drug_allergy_repository import DrugAllergyRepository
from repos.client.food_allergy_repository import FoodAllergyRepository
from repos.client.life_style_repository import ClientLifestyleRepository
from repos.client.notification_repository import NotificationRepository
from repos.client.vital_rpository import VitalsRepository

logger = logging.getLogger(__name__)

from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from typing import Dict, Any, List


class ClientRepository:

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)
        self.notification = NotificationRepository(session)
        self.session = session
        self.vital_repository = VitalsRepository(session)
        self.col = [
            Client.id,
            Client.photo,
            Client.address,
            Client.date_of_birth,
            Client.marital_status,  # Assuming this field exists in the Client model
            # Lga.state_id, # caused a terrible bug in get_all_client function. should be reviewed before re-enabling
            Client.lga_id,
            Client.occupation_id,
            Client.blood_group,
            Person.phone,
            Person.email,
            Person.sex,
            Person.last_name,
            Person.first_name,
            Person.middle_name,
            Person.enrollment_date,
        ]

    def add_client(self, client: ClientDTO):
        try:
            # Create Person instance
            person = Person(
                title=client.title,
                first_name=client.first_name,
                last_name=client.last_name,
                middle_name=client.middle_name,
                sex=client.sex,
                email=client.email,
                phone=client.phone,
            )
            self.session.add(person)
            self.session.flush()  # Flush to get person.id without committing

            # Ensure required fields are present
            if not client.locality or not client.locality.lga_id:
                raise ValueError("LGA ID is required.")
            if not client.occupation or not client.occupation.id:
                raise ValueError("Occupation ID is required.")

            if client.user_account is not None \
                    and client.user_account.username \
                    and client.user_account.password:
                # client.user_account.status = AccountStatus.Active
                # client.user_account.person_id = person.id
                user = {
                    "username": client.user_account.username,
                    "password": client.user_account.password,
                    "status": AccountStatus.Active,
                    "person_id": person.id,
                }

                self.user_repository.create_user(User(**user))
            else:
                # Create Client instance
                new_client = Client(
                    photo=client.photo,
                    marital_status=client.marital_status,
                    date_of_birth=client.date_of_birth,
                    blood_group=client.blood_group,
                    address=client.address,
                    lga_id=client.locality.lga_id,
                    occupation_id=client.occupation.id,
                    person_id=person.id
                )
                self.session.add(new_client)

                # Commit once to ensure atomicity
                self.session.commit()
                self.session.refresh(new_client)

            return person.id

        except (SQLAlchemyError, ValueError) as e:
            self.session.rollback()  # Rollback transaction in case of failure
            raise e  # Rethrow the error for logging or higher-level handling

    def update_client(self, client_id: int, client_data: ClientDTO):
        """
        Updates a Client and corresponding Person record based on the provided ClientDTO.

        :param client_id: The ID of the client to update.
        :param client_data: A ClientDTO object containing the updated data.
        :return: The updated client object.
        """
        try:
            # Fetch the Client record
            client = self.session.query(Client).filter_by(id=client_id).first()
            if not client:
                raise ValueError(f"Client with ID {client_id} not found.")

            # Fetch the associated Person record
            person = self.session.query(Person).filter_by(id=client.person_id).first()
            if not person:
                raise ValueError(f"Person with ID {client.person_id} not found.")

            # Update Person details
            person.first_name = client_data.first_name
            person.middle_name = client_data.middle_name
            person.last_name = client_data.last_name
            person.sex = client_data.sex
            # person.email = client_data.email
            person.phone = client_data.phone
            person.title = client_data.title

            # Update Client details
            client.photo = client_data.photo
            client.marital_status = client_data.marital_status
            client.date_of_birth = client_data.date_of_birth
            client.blood_group = client_data.blood_group
            client.address = client_data.address

            # Handle optional fields carefully
            if client_data.locality:
                client.lga_id = client_data.locality.lga_id
            if client_data.occupation:
                client.occupation_id = client_data.occupation.id
            # if client.user_account is not None \
            #         and client.user_account.username \
            #         and client.user_account.password:
            #     # Update user account details
            #     pass
            # Commit once for atomic update
            self.session.commit()
            self.session.refresh(client)

            return client

        except (SQLAlchemyError, ValueError) as e:
            self.session.rollback()  # Rollback transaction in case of failure
            raise e  # Re-raise exception for logging or higher-level handling

    # def get_all_client(self, skip: int = 0, limit: int = 100, keyword: str = ''):
    #     query = self.session.query(*self.col) \
    #         .join(Person, Person.id == Client.person_id) \
    #         .join(Occupation, Client.occupation_id == Occupation.id)
    #
    #     if len(keyword) > 3:
    #         print('Search initiated')
    #         query = query.filter(Person.first_name.ilike(f"%{keyword}%") |
    #                              Person.last_name.ilike(f"%{keyword}%") |
    #                              Person.phone.ilike(f"%{keyword}%") |
    #                              Client.date_of_birth.ilike(f"%{keyword}%"))
    #
    #     query = query.offset(skip).limit(limit).all()
    #     data = []
    #
    #     for rs in query:
    #         data.append(
    #             {
    #                 'id': rs.id,
    #                 'photo': rs.photo,
    #                 'address': rs.address,
    #                 'sex': rs.sex,
    #                 'enrollment_date': rs.enrollment_date,
    #                 'date_of_birth': rs.date_of_birth,
    #                 'marital_status': 'Single',
    #                 'blood_group': rs.blood_group,
    #                 'phone': rs.phone,
    #                 'email': rs.email,
    #                 'first_name': rs.first_name,
    #                 'last_name': rs.last_name,
    #                 'middle_name': rs.middle_name
    #             }
    #         )
    #
    #     return dict(
    #         data=data,
    #         total=self.get_client_count(keyword)
    #     )

    from typing import Dict, List, Any
    import logging

    logger = logging.getLogger(__name__)

    def get_all_client(self, skip: int, limit: int, keyword: str = '') -> Dict[str, Any]:
        """
        Retrieve a list of clients with optional filtering and pagination.

        :param skip: Number of records to skip (for pagination).
        :param limit: Maximum number of records to return (for pagination).
        :param keyword: Optional keyword to filter clients by first name, last name, phone, or date of birth.
        :return: A dictionary containing the list of clients and the total count.
        """
        print('limit', limit)
        try:
            # self.insert_data_from_csv()
            query = self.session.query(*self.col) \
                .join(Person, Person.id == Client.person_id) \
                .join(Occupation, Client.occupation_id == Occupation.id)

            if len(keyword) > 3:
                query = query.filter(
                    or_(Person.first_name.ilike(f"%{keyword}%"),
                        Person.last_name.ilike(f"%{keyword}%"),
                        Person.phone.ilike(f"%{keyword}%"),
                        cast(Client.date_of_birth, String).ilike(f"%{keyword}%")
                        )
                )

            query = query.offset(skip).limit(limit).all()
            data = []

            for rs in query:
                data.append({
                    'id': rs.id,
                    'photo': rs.photo,
                    'address': rs.address,
                    'sex': rs.sex,
                    'enrollment_date': rs.enrollment_date,
                    'date_of_birth': rs.date_of_birth,
                    'marital_status': rs.marital_status,  # Use the actual value from the database
                    'blood_group': rs.blood_group,
                    'phone': rs.phone,
                    'email': rs.email,
                    'first_name': rs.first_name,
                    'last_name': rs.last_name,
                    'middle_name': rs.middle_name,
                    'notifications': self.notification.get_subscriptions_by_client(rs.id, 100, 0)
                })

            return {
                'data': data,
                'total': self.get_client_count(keyword)
            }

        except Exception as e:
            logger.error('Error retrieving clients: %s', e)
            raise  # Re-raise the exception after logging

    # def get_all_client(
    #         self,
    #         skip: int = 0,
    #         limit: int = 100,
    #         keyword: str = ''
    # ) -> Dict[str, Any]:
    #     """
    #     Optimized: Retrieve clients with filtering, pagination, eager loading,
    #     and bulk notifications fetch.
    #     """
    #
    #     try:
    #         # Base query with eager loading to prevent lazy-load queries
    #         query = (
    #             self.session.query(Client)
    #             .join(Person, Person.id == Client.person_id)
    #             .join(Occupation, Client.occupation_id == Occupation.id)
    #             .options(
    #                 joinedload(Client.person),
    #                 joinedload(Client.occupation),
    #             )
    #         )
    #
    #         # Filtering by keyword
    #         if keyword and len(keyword) > 1:  # allow shorter searches
    #             search = f"%{keyword}%"
    #             query = query.filter(
    #                 or_(
    #                     Person.first_name.ilike(search),
    #                     Person.last_name.ilike(search),
    #                     Person.phone.ilike(search),
    #                     func.to_char(Client.date_of_birth, "YYYY-MM-DD").ilike(search),  # better than cast
    #                 )
    #             )
    #
    #         # Total count (efficiently)
    #         total = query.with_entities(func.count(Client.id)).scalar()
    #
    #         # Apply pagination
    #         clients: List[Client] = query.offset(skip).limit(limit).all()
    #
    #         # Bulk fetch notifications instead of N+1
    #         client_ids = [c.id for c in clients]
    #         notif_map = self.notification.get_subscriptions_by_client(client_ids, 100, 0)
    #
    #         # Build response
    #         data = [
    #             {
    #                 "id": c.id,
    #                 "photo": c.photo,
    #                 "address": c.address,
    #                 "sex": c.sex,
    #                 "enrollment_date": c.enrollment_date,
    #                 "date_of_birth": c.date_of_birth,
    #                 "marital_status": c.marital_status,
    #                 "blood_group": c.blood_group,
    #                 "phone": c.person.phone,
    #                 "email": c.person.email,
    #                 "first_name": c.person.first_name,
    #                 "last_name": c.person.last_name,
    #                 "middle_name": c.person.middle_name,
    #                 "notifications": notif_map.get(c.id, []),
    #             }
    #             for c in clients
    #         ]
    #
    #         return {"data": data, "total": total}
    #
    #     except Exception as e:
    #         logger.error("Error retrieving clients: %s", e, exc_info=True)
    #         raise

    def get_client_count(self, keyword: str = ''):
        if keyword:
            search = f"%{keyword}%"
            return self.session.query(Client) \
                .join(Person, Client.person_id == Person.id) \
                .filter(
                or_(
                    Person.first_name.ilike(search),
                    Person.last_name.ilike(search),
                    Person.phone.ilike(search),
                    cast(Client.date_of_birth, String).ilike(search)
                )
            ).count()
        else:
            return self.session.query(Client).count()

    def get_client(self, client_id: int):
        # print('client id', client_id)

        drug_allergy_repository = DrugAllergyRepository(self.session)
        food_allergy_repository = FoodAllergyRepository(self.session)
        lifestyle_repository = ClientLifestyleRepository(self.session)

        cols = [
            Client.id,
            Person.first_name,
            Person.last_name,
            Person.middle_name,
            Person.email,
            Person.phone,
            Client.photo,
            Client.date_of_birth,
            Client.address,
            Client.blood_group,
            Person.sex,
            Person.enrollment_date,
            # Client.marital_status,
            Lga.lga,
            Lga.state_id,
            Lga.id.label("lga_id"),
            Occupation.id.label("occupation_id"),
        ]
        rs = self.session.query(*cols).select_from(Client) \
            .join(Person, Person.id == Client.person_id) \
            .join(Lga, Lga.id == Client.lga_id) \
            .join(Occupation, Occupation.id == Client.occupation_id) \
            .filter(Client.id == client_id).one_or_none()

        if rs:
            return {
                'id': rs.id,
                'first_name': rs.first_name,
                'last_name': rs.last_name,
                'middle_name': rs.middle_name,
                'email': rs.email,
                'phone': rs.phone,
                'photo': rs.photo,
                'date_of_birth': rs.date_of_birth,
                'address': rs.address,
                'blood_group': rs.blood_group,
                'sex': rs.sex,
                'enrollment_date': rs.enrollment_date,
                'marital_status': 'Single',
                'locality': (self.get_lga(rs.lga_id)).__dict__,
                'occupation': (self.get_occupation(rs.occupation_id)).__dict__,
                'notifications': self.notification.get_subscriptions_by_client(rs.id, 100, 0),
                'vitals': self.vital_repository.get_vitals_by_client_id(rs.id, 0, 100)['data'],
                'food_allergy': food_allergy_repository.get_by_client(rs.id),
                'drug_allergy': drug_allergy_repository.get_by_client(rs.id),
                'lifestyle': lifestyle_repository.get_by_patient(rs.id)
            }
        else:
            raise ValueError(f"Client with ID {client_id} not found.")
            return None

    def get_occupation(self, occupation_id: int) -> Optional[OccupationDTO]:
        occupation = self.session.query(Occupation).filter(Occupation.id == occupation_id).one_or_none()
        if occupation is None:
            return None
        return OccupationDTO(id=occupation.id, occupation=occupation.occupation)

    def get_lga(self, lga_id: int) -> Optional[LocalityDTO]:
        cols = [
            Lga.id,
            Lga.lga,
            State.id.label("state_id"),
            State.state
        ]

        locality = (
            self.session.query(*cols)
            .join(State, State.id == Lga.state_id)
            .filter(Lga.id == lga_id)
            .one_or_none()  # Avoids exceptions when no result is found
        )

        if locality is None:
            return None

        return LocalityDTO(lga_id=locality.id, state_id=locality.state_id, state=locality.state, lga=locality.lga)

    def get_state_lga(self, state_id: int):
        return self.session.query(Lga).where(Lga.state_id == state_id).all()

    def get_states(self):
        try:
            states = self.session.query(State).order_by(State.state).all()
            return [state for state in states]
        except Exception as e:
            print(f"Error fetching states: {e}")
            return []

    def get_occupations(self, limit: int = 20, skip: int = 0):
        return self.session.query(Occupation).offset(skip).limit(limit).all();

    def add_people_to_org(self, person: Client):
        org_person = OrganizationPeople(

        )
        self.session.add(org_person)
        self.session.refresh(org_person)
        return org_person;

    def is_email_unique(self, email: str) -> bool:
        client = self.session.query(Person) \
            .filter(Person.email == email) \
            .one_or_none()
        if client:
            return False
        return True

    def search_client(self, searchtext: str):

        try:
            query = self.session.query(*self.col).select_from(Client) \
                .join(Person, Person.id == Client.person_id) \
                .join(Lga, Lga.id == Client.lga_id) \
                .where((Person.first_name.ilike(f"%{searchtext}%")) |
                       (Person.last_name.ilike(f"%{searchtext}%")) |
                       (Person.phone.ilike(f"%{searchtext}%"))
                       ).all()

            # == searchtext or Person.last_name == searchtext or Client.date_of_birth == searchtext)).all()

            response = []
            for client in query:
                response.append(
                    {
                        'id': client.id,
                        'first_name': client.first_name,
                        'last_name': client.last_name,
                        'middle_name': client.middle_name,
                        'email': client.email,
                        'phone': client.phone,
                        'photo': client.photo,
                        'date_of_birth': client.date_of_birth,
                        'address': client.address,
                        'blood_group': client.blood_group,
                        'sex': client.sex,
                        'enrollment_date': client.enrollment_date,
                        'marital_status': 'Single',
                        'lga_id': client.lga_id,
                        'occupation_id': client.occupation_id,
                        # 'state_id': client.state_id,
                    }
                )
            return response
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return []

        # elif txt.count() == 2:
        #     return db.query(Client).where(Client.first_name == txt[0] |
        #               Client.last_name == txt[0] |
        #               Client.date_of_birth == txt[0] |
        #               Client.first_name == txt[1] |
        #               Client.last_name == txt[1] |
        #               Client.date_of_birth == txt[1]
        #         ).all()
        # elif txt.count() == 3:
        #     return db.query(Client).where(Client.first_name == txt[0] |
        #               Client.last_name == txt[0] |
        #               Client.date_of_birth == txt[0] |
        #               Client.first_name == txt[1] |
        #               Client.last_name == txt[1] |
        #               Client.date_of_birth == txt[1] |
        #               Client.first_name == txt[2] |
        #               Client.last_name == txt[2] |
        #               Client.date_of_birth == txt[2]
        #
        #         ).all()

    def safe_parse_date(self, date_string):
        try:
            return datetime.strptime(date_string, "%Y-%m-%d").date() if date_string else None
        except ValueError:
            print(f"Invalid date format: {date_string}")
            return None

    def safe_get(self, row, index):
        return row[index] if len(row) > index else None

    def insert_data_from_csv(self):
        session = self.session

        # Get the absolute path of the current script
        current_script_path = Path(__file__).resolve()
        csv_file = current_script_path.parent.parent.parent / "bootstrap" / "migration" / "patients.csv"

        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header row if needed

            batch_size = 50  # Adjust based on database performance
            batch = []

            for row in reader:
                try:
                    phone = self.safe_get(row, 3)
                    first_name = self.safe_get(row, 2)
                    last_name = self.safe_get(row, 1)
                    sex = self.safe_get(row, 5)
                    email = self.safe_get(row, 7)
                    enrollment_date = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S").date()
                    date_of_birth = self.safe_parse_date(self.safe_get(row, 9))
                    address = self.safe_get(row, 6)
                    marital_status = self.safe_get(row, 11)

                    # # Check if person exists
                    # existing_person = session.query(Person).filter_by(phone=phone).first()
                    # if existing_person:
                    #     print(f"Updating existing person with phone {phone}")
                    #     existing_person.first_name = first_name
                    #     existing_person.last_name = last_name
                    #     existing_person.sex = sex
                    #     existing_person.email = email
                    #     existing_person.enrollment_date = enrollment_date
                    # else:
                    person = Person(
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=None,
                        sex=sex,
                        email=email,
                        phone=phone,
                        enrollment_date=enrollment_date
                    )
                    session.add(person)
                    session.flush()  # Assign ID

                    client_id = self.safe_get(row, 0)
                    # client = session.query(Client).filter(Client.id==client_id).first()
                    # if client:
                    #     print(f"Updating existing client with ID {client_id}")
                    #     client.marital_status = marital_status
                    #     client.date_of_birth = date_of_birth
                    #     client.address = address
                    # else:
                    print('client id', client_id)
                    client = Client(
                        id=client_id,
                        person_id=person.id,
                        marital_status=marital_status,
                        date_of_birth=date_of_birth,
                        blood_group=None,
                        address=address,
                        lga_id=1,  # Default
                        occupation_id=1  # Default
                    )
                    session.add(client)

                    batch.append(client)

                    if len(batch) >= batch_size:
                        session.commit()
                        batch.clear()

                    print(f"Processed {first_name} {last_name}")

                except IntegrityError:
                    session.rollback()
                    print(f"Skipping duplicate entry for client ID {client_id}")
                except Exception as e:
                    session.rollback()
                    print(f"Error processing data: {e}")

            if batch:
                session.commit()
