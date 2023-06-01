from commands.people import Client
from sqlalchemy.orm import Session

from models.people import People


def add_client(db: Session, client: Client):
    new_client = People(
        photo=client.photo,
        first_name=client.first_name,
        last_name=client.last_name,
        sex=client.sex,
        marital_status=client.marital_status,
        date_of_birth=client.date_of_birth,
        blood_group=client.blood_group,
        email=client.email,
        phone=client.phone,
        address=client.lga_id,
        lga_id=client.lga_id,
        occupation_id=client.occupation
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


def get_all_client(db: Session, skip: int = 0, limit: int = 100):
    return db.query(People).offset(skip).limit(limit).all()

