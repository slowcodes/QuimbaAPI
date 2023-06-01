from faker import Faker
from fastapi import APIRouter, HTTPException, Depends, security, Security
from starlette import status

from commands.people import Client
from sqlalchemy.orm import Session
import repos
from db import get_db
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from repos import client_repository

client_router = APIRouter()


@client_router.get('/api/clients/', tags=['Clients'])
def get_all_clients(skip: int, limit: int, db: Session = Depends(get_db)):
    # faker = Faker()
    # for i in range(3000):
    #     new_client = Client(
    #         photo=faker.word(),
    #         first_name=faker.unique.first_name(),
    #         last_name=faker.unique.first_name(),
    #         middle_name=faker.unique.first_name(),
    #         sex='Male',
    #         marital_status='Single',
    #         date_of_birth=faker.date(),
    #         blood_group='A+',
    #         email=faker.unique.email(),
    #         phone=faker.phone_number(),
    #         address=faker.address(),
    #         lga_id=12,
    #         occupation=1
    #     )
    #     repos.client_repository.add_client(db, new_client)
    return repos.client_repository.get_all_client(db, skip, limit)


@client_router.post('/api/clients/enroll', response_model=None, tags=['Clients', 'Enrollment'])
def enroll_client(client: Client, db: Session = Depends(get_db)):
    enrolled_client = repos.client_repository.add_client(db, client)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=dict(
        msg='Client successfully registered with ID' + str(enrolled_client.id)))


@client_router.get('/api/clients/check_email', response_model=None, tags=['Clients', 'Enrollment', 'Username'])
def check_client_username(email: str, db: Session = Depends(get_db)):
    exist = repos.client_repository.is_email_unique(db, email)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={'msg': exist})


@client_router.get('/api/staff/', tags=['Staff'])
def get_all_staff():
    return repos.client_repository.get_all_staff()


@client_router.post('/api/staff/enroll', tags=['Staff', 'Enrollment'])
def enroll_Staff(client: Client):
    return repos.client_repository.enroll_staff()


@client_router.get('/api/resources/states/', tags=['State', 'Resources'])
def get_states(db: Session = Depends(get_db)):
    return repos.client_repository.get_states(db)


@client_router.get('/api/resources/states/lga/', tags=['State', 'Resources', 'LGA'])
def get_state_lga(state_id: int, db: Session = Depends(get_db)):
    return repos.client_repository.get_state_lga(db, state_id)


@client_router.get('/api/resources/occupations/', tags=['Occupation', 'Resources'])
def get_occupations(db: Session = Depends(get_db)):
    return repos.client_repository.get_occupations(db)


@client_router.get('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def get_registered_orgs(db: Session = Depends(get_db)):
    return repos.client_repository.get_registered_orgs(db)
