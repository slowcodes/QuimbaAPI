from sqlalchemy.orm import Session

from commands.people import Client
from models.client import *
from db import session, engine


def add_client(db: Session, client: Client):
    new_client = Client(
        photo=client.photo,
        first_name=client.first_name,
        last_name=client.last_name,
        middle_name=client.middle_name,
        sex=client.sex,
        marital_status=client.marital_status,
        date_of_birth=client.date_of_birth,
        blood_group=client.blood_group,
        email=client.email,
        phone=client.phone,
        address=client.address,
        lga_id=client.lga_id,
        occupation_id=client.occupation
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return new_client


def get_all_client(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Client).join(Occupation, Client.occupation_id == Occupation.id).offset(skip).limit(limit).all()


def get_state_lga(db: Session, state_id: int):
    return db.query(Lga).where(Lga.state_id == state_id).all()


def get_states(db: Session):
    return db.query(State).all()


def enroll_staff():
    return None


def get_all_staff():
    return None


def get_occupations(db: Session):
    return db.query(Occupation).all()


def get_registered_orgs(db: Session):
    return db.query(Organization).all();


def add_people_to_org(db: Session, person: Client):
    org_person = OrganizationPeople(

    )
    db.add(org_person)
    db.refresh(org_person)
    return org_person;


def is_email_unique(db: Session, email: str):
    client = db.query(Client).where(Client.email == email).count()
    if client <= 0:
        return False
    return True
