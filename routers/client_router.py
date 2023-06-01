from fastapi import APIRouter, HTTPException, Depends, security, Security
from commands.people import Client
import repos

client_router = APIRouter()


@client_router.get('/api/clients/', tags=['Clients'])
def get_all_clients():
    return repos.client_repository.get_all_client()


@client_router.post('/api/clients/enroll', tags=['Clients', 'Enrollment'])
def enroll_client(client: Client):
    return repos.client_repository.add_client()

