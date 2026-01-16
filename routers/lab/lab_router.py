from fastapi import APIRouter, Depends, Query
from starlette import status

from dtos.lab import LaboratoryDTO, LaboratoryGroupDTO, LaboratoryServiceDetailDTO, LabServicesQueueDTO, LabServiceDTO
from sqlalchemy.orm import Session
from db import get_db
from starlette.responses import JSONResponse

from repos.lab.lab_repository import LabRepository

lab_router = APIRouter()


def get_lab_repository(db: Session = Depends(get_db)):
    return LabRepository(db)


@lab_router.get('/api/laboratories/labs', tags=['Laboratories'])
def get_all_labs(
    skip: int,
    limit: int,
    keyword: str = Query(None, description="Search keyword for lab name"),
    lab_repository: LabRepository = Depends(get_lab_repository),
):
    return lab_repository.get_all_labs(skip, limit, keyword=keyword)


@lab_router.get('/api/laboratories/groups', tags=['Laboratories', 'Laboratory Groups'])
def get_all_lab_groups(skip: int, limit: int, search_text: str,
                       lab_repository: LabRepository = Depends(get_lab_repository)):
    return dict(lab_repository.get_all_labs_groups(skip, limit, search_text))


@lab_router.post('/api/laboratories/add_lab', tags=['Laboratories', 'Laboratory'])
def add_lab(lab: LaboratoryDTO, lab_repository: LabRepository = Depends(get_lab_repository)):
    if lab.id:
        lab_repository.update_lab(lab)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content=dict(error=False, msg='Lab service updated successfully'))

    if lab_repository.add_lab(lab):
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=dict(error=False, msg='Lab added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        content=dict(error=False, msg='New lab must unique. A similar entry already exist'))


@lab_router.post('/api/laboratories/groups/add', tags=['Laboratories', 'Laboratory Groups'])
def add_lab_group(labGroup: LaboratoryGroupDTO, lab_repository: LabRepository = Depends(get_lab_repository)):
    if lab_repository.add_lab_group(labGroup):
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=dict(error=False, msg='Lab group added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,

                        content=dict(error=False, msg='New lab group must unique. A similar entry already exist'))


@lab_router.put('/api/laboratories/lab_service', tags=['Laboratories' 'Laboratory Service'])
def update_lab_service(lab_service: LaboratoryServiceDetailDTO,
                       lab_repository: LabRepository = Depends(get_lab_repository)):
    if lab_service.lab_service_id:
        lab_repository.update_lab_service_detail(lab_service.lab_service_id, lab_service)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content=dict(error=False, msg='Lab service updated  nbqz'))
    else:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content=dict(error=True, msg='Lab service subject not found'))


@lab_router.delete('/api/laboratories/lab_service', tags=['Laboratories' 'Laboratory Service'])
def delete_lab_service(lab_service_id: int, lab_repository: LabRepository = Depends(get_lab_repository)):
    if lab_repository.soft_delete_lab_service_detail(lab_service_id):
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content=dict(error=False, msg='Lab service deleted'))
    else:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content=dict(error=True, msg='Lab service subject not found'))


@lab_router.put('/api/laboratories/lab_service_detail', tags=['Laboratories' 'Laboratory Service'])
def update_lab_service(lab_service: LabServiceDTO,
                       lab_repository: LabRepository = Depends(get_lab_repository)):
    if lab_service.id:
        lab_repository.update_lab_service_detail(lab_service.id, lab_service)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content=dict(error=False, msg='Lab service updated  nbqz'))
    else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=dict(error=True, msg='Lab service subject not found'))


@lab_router.post('/api/laboratories/lab_service', tags=['Laboratories', 'Laboratory Service Detail'])
def add_lab_services_detail(lab_service: LaboratoryServiceDetailDTO,
                            lab_repository: LabRepository = Depends(get_lab_repository)):
    if lab_repository.add_lab_services(lab_service):
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=dict(error=False, msg='Lab service added successfully'))
    return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        content=dict(error=False, msg='New lab service must unique. A similar entry already exist'))


@lab_router.get('/api/laboratories/services', tags=['Laboratories', 'Laboratory Service'])
def get_all_lab_services(lab_repository: LabRepository = Depends(get_lab_repository), skip: int = 0, limit: int = 10,
                         lab_id: int = 1, search=''):
    return lab_repository.get_lab_services(skip, limit, lab_id, search)


@lab_router.get('/api/laboratories/services/group/', tags=['Laboratories', 'Laboratory Service', 'Group Tags'])
def get_lab_service_groups(lab_id: int = 0, lab_repository: LabRepository = Depends(get_lab_repository)):
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=dict(error=False, msg=lab_repository.get_lab_group(lab_id)))


@lab_router.get('/api/laboratories/services/lab_service_details/', response_model=LabServiceDTO,
                tags=['Laboratories', 'Laboratory Service', 'Details'])
def get_lab_service_details(lab_id: int, repo: LabRepository = Depends(get_lab_repository)):
    return repo.get_lab_service_details(lab_id)


@lab_router.get('/api/laboratories/current-state/',
                tags=['Laboratories', 'Laboratory Service', 'Details'])
def get_current_state(lab_id: int, repo: LabRepository = Depends(get_lab_repository)):
    return repo.get_current_state(lab_id)
