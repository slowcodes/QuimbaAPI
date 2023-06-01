from faker import Faker
from fastapi import APIRouter, HTTPException, Depends, security, Security
from starlette import status

from commands.lab import Laboratory, LaboratoryGroup, LaboratoryService
from commands.people import Client
from sqlalchemy.orm import Session
import repos.lab_repository
from db import get_db
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from repos import client_repository

lab_router = APIRouter()


@lab_router.get('/api/laboratories/labs', tags=['Laboratories'])
def get_all_labs(skip: int, limit: int, db: Session = Depends(get_db)):
    return repos.lab_repository.get_all_labs(db, skip, limit)


@lab_router.get('/api/laboratories/groups', tags=['Laboratories', 'Laboratory Groups'])
def get_all_labs(skip: int, limit: int, db: Session = Depends(get_db)):
    return repos.lab_repository.get_all_labs_groups(db, skip, limit)


@lab_router.post('/api/laboratories/add_lab', tags=['Laboratories', 'Laboratory'])
def add_lab(lab: Laboratory, db: Session = Depends(get_db)):
    if (repos.lab_repository.add_lab(db, lab)):
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=dict(error=False, msg='Lab added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        content=dict(error=False, msg='New lab must unique. A similar entry already exist'))


@lab_router.post('/api/laboratories/groups/add', tags=['Laboratories', 'Laboratory Groups'])
def add_lab_group(labGroup: LaboratoryGroup, db: Session = Depends(get_db)):
    if repos.lab_repository.add_lab_group(db, labGroup):
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=dict(error=False, msg='Lab group added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        content=dict(error=False, msg='New lab group must unique. A similar entry already exist'))


@lab_router.post('/api/laboratories/add_lab_service', tags=['Laboratories', 'Laboratory Service'])
def add_lab_services(labService: LaboratoryService, db: Session = Depends(get_db)):
    if repos.lab_repository.add_lab_services(db, labService):
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=dict(error=False, msg='Lab service added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        content=dict(error=False, msg='New lab service must unique. A similar entry already exist'))
