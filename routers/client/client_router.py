from fastapi import APIRouter, Depends
from starlette import status

from commands.people import ClientCommand, OrganisationDTO
from sqlalchemy.orm import Session
from db import get_db
from starlette.responses import JSONResponse

from repos.client.client_repository import ClientRepository

client_router = APIRouter()


def get_client_repository(db: Session = Depends(get_db)) -> ClientRepository:
    return ClientRepository(db)


@client_router.get('/api/clients/', tags=['Clients'])
def get_all_clients(skip: int = 0,
                    limit: int = 100, keyword: str = '',
                    repo: ClientRepository = Depends(get_client_repository)):
    # faker = Faker()
    # for i in range(3000):
    #     new_client = ClientCommand(
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
    #         lga_id=10,
    #         occupation=1
    #     )
    #     repos.client_repository.add_client(db, new_client)
    return repo.get_all_client(skip, limit, keyword)


@client_router.get('/api/clients/client', response_model=None, tags=['Clients'])
def get_client(id: int, repo: ClientRepository = Depends(get_client_repository)):
    # return JSONResponse(status_code=status.HTTP_200_OK, content=repos.client_repository.get_client(db, id))
    return repo.get_client(id);


@client_router.post('/api/clients/enroll', response_model=None, tags=['Clients', 'Enrollment'])
def enroll_client(client: ClientCommand, repo: ClientRepository = Depends(get_client_repository)):

    if client.id:
        update = repo.update_client(client)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=dict(
            msg='Client successfully registered with ID' + str(update.id)))
    enrolled_client = repo.add_client(client)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=dict(
        msg='Client successfully registered with ID' + str(enrolled_client.id)))


@client_router.get('/api/clients/check_email', response_model=None, tags=['Clients', 'Enrollment', 'Username'])
def check_client_username(email: str, repo: ClientRepository = Depends(get_client_repository)):

    exist = repo.is_email_unique(email)
    return exist
    # JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={'msg': exist})


@client_router.get('/api/clients/search', response_model=None, tags=['Clients', 'Search'])
def search_client(searchtext: str, repo: ClientRepository = Depends(get_client_repository)):
    return repo.search_client(searchtext)


@client_router.get('/api/staff/', tags=['Staff'])
def get_all_staff(repo: ClientRepository = Depends(get_client_repository)):
    return repo.get_all_staff()


@client_router.post('/api/staff/enroll', tags=['Staff', 'Enrollment'])
def enroll_Staff(client: ClientCommand, repo: ClientRepository = Depends(get_client_repository)):
    return repo.enroll_staff(client)


@client_router.get('/api/resources/states/', tags=['State', 'Resources'])
def get_states(repo: ClientRepository = Depends(get_client_repository)):
    res = repo.get_states()
    return res


@client_router.get('/api/resources/states/lga/', tags=['State', 'Resources', 'LGA'])
def get_state_lga(state_id: int, repo: ClientRepository = Depends(get_client_repository)):
    return repo.get_state_lga(state_id)


@client_router.get('/api/resources/occupations/', tags=['Occupation', 'Resources'])
def get_occupations(repo: ClientRepository = Depends(get_client_repository)):
    return repo.get_occupations()


@client_router.get('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def get_registered_orgs(skip: int = 0, limit: int = 100, repo: ClientRepository = Depends(get_client_repository)):
    return repo.get_registered_orgs(limit, skip)


@client_router.post('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def add_registered_orgs(org: OrganisationDTO,  repo: ClientRepository = Depends(get_client_repository)):
    return repo.add_registered_org(org)


@client_router.delete('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def delete_registered_ord(org: OrganisationDTO, repo: ClientRepository = Depends(get_client_repository)):
    return repo.delete_registered_org(org)


@client_router.put('/api/resources/registered-orgs/', tags=['Organization', 'Resources'])
def update_registered_ord(org: OrganisationDTO, repo: ClientRepository = Depends(get_client_repository)):
    return repo.update_registered_org(org)