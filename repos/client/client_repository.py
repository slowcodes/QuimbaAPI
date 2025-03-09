from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session
from commands.people import ClientCommand, OrganisationDTO, LocalityDTO, OccupationDTO
from models.client import Client, Occupation, Lga, State, OrganizationPeople, Organization, Person
import logging

from repos.client.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class ClientRepository:

    def __init__(self, session: Session):
        self.notification = NotificationRepository(session)
        self.session = session
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



    def add_client(self, client: ClientCommand):
        person = Person(
            first_name=client.first_name,
            last_name=client.last_name,
            middle_name=client.middle_name,
            sex=client.sex,
            email=client.email,
            phone=client.phone,
        )
        self.session.add(person)
        self.session.commit()
        self.session.refresh(person)

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
        self.session.commit()
        self.session.refresh(new_client)

        return new_client


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

    def get_all_client(self, skip: int = 0, limit: int = 100, keyword: str = '') -> Dict[str, Any]:
        """
        Retrieve a list of clients with optional filtering and pagination.

        :param skip: Number of records to skip (for pagination).
        :param limit: Maximum number of records to return (for pagination).
        :param keyword: Optional keyword to filter clients by first name, last name, phone, or date of birth.
        :return: A dictionary containing the list of clients and the total count.
        """
        try:

            query = self.session.query(*self.col) \
                .join(Person, Person.id == Client.person_id) \
                .join(Occupation, Client.occupation_id == Occupation.id)

            if len(keyword) > 3:
                query = query.filter(Person.first_name.ilike(f"%{keyword}%") |
                                     Person.last_name.ilike(f"%{keyword}%") |
                                     Person.phone.ilike(f"%{keyword}%") |
                                     Client.date_of_birth.ilike(f"%{keyword}%"))

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

    def get_client_count(self, keyword: str = ''):
        return self.session.query(*self.col) \
            .filter(Person.first_name.ilike(f"%{keyword}%") |
                    Person.last_name.ilike(f"%{keyword}%") |
                    Person.phone.ilike(f"%{keyword}%") |
                    Client.date_of_birth.ilike(f"%{keyword}%")).count() if (len(keyword) > 0) else self.session.query(
            Client).count()

    def get_client(self, client_id: int):
        print('client id', client_id)
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
            .filter(Client.id == client_id).one()

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
            'locality': self.get_lga(rs.lga_id),
            'occupation': self.get_occupation(rs.occupation_id),
            'notifications': self.notification.get_subscriptions_by_client(rs.id, 100, 0)
        }

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

    def enroll_staff(self):
        return None

    def get_all_staff(self):
        return None

    def get_occupations(self, limit: int = 20, skip: int = 0):
        return self.session.query(Occupation).offset(skip).limit(limit).all();

    def get_registered_orgs(self, limit, skip):
        all = self.session.query(Organization)
        return {
            'total': all.count(),
            'data': all.offset(skip).limit(limit).all()
        }

    def add_registered_org(self, org_dto: OrganisationDTO):
        org = Organization(**org_dto.__dict__)  # assuming `OrganisationDTO` has fields matching `Organization`
        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)
        return org

    def delete_registered_org(self, org_id: int):
        org = self.session.query(Organization).filter(Organization.id == org_id).one()
        if org:
            self.session.delete(org)
            self.session.commit()
            return True
        return False

    def update_registered_org(self, org_dto: OrganisationDTO):
        org = self.session.query(Organization).filter(Organization.id == org_dto.id).first()
        if org:
            data = org_dto.dict(exclude_unset=True)
            for key, value in data.items():
                setattr(org, key, value)
            self.session.commit()
            return True
        return False

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
