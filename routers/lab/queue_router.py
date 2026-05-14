import json
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from security.dependencies import get_current_active_user
from sqlalchemy.orm import Session

from cache.redis import get_redis_client
from db import get_db
from dtos.lab import DynamicParameterBaseDTO, DynamicParameterCreateDTO, DynamicParameterDTO, \
    DynamicParameterUpdateDTO, LabServicesQueueDTO, LabServicesQueueCreateDTO
from dtos.auth import UserDTO
from repos.lab.queue_repository import QueueRepository

queue_router = APIRouter(prefix="/api/lab-services-queue", tags=["Lab Services Queue"])


def get_queue_repository(db: Session = Depends(get_db)):
    return QueueRepository(db)


@queue_router.post("/", response_model=LabServicesQueueDTO)
def create_lab_service_queue(queue: LabServicesQueueCreateDTO,
                             qr: QueueRepository = Depends(get_queue_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    if queue.lab_service_id not in [None, 0]:
        return qr.create_lab_service_queue(queue)


@queue_router.get("/{queue_id}", response_model=LabServicesQueueDTO)
def read_lab_service_queue(queue_id: int,  qr: QueueRepository = Depends(get_queue_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_lab_service_queue = qr.get_queue(queue_id=queue_id)
    if db_lab_service_queue is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return db_lab_service_queue


@queue_router.get("/")
def read_lab_service_queue(lab_id: int = 0, skip: int = 0, limit: int = 10, booking_id: int = 0,
                           search_text: str = '', last_date: str = None,
                           start_date: str = None, status: str = None, refresh: int = 0, client_id: int = 0,
                           lab_service_id: int = 0,  qr: QueueRepository = Depends(get_queue_repository),*,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):

    redis = get_redis_client()
    cache_key = f"lab_queue:{skip}:{limit}:{booking_id}:{last_date}:{start_date}:{status}:{client_id}:{lab_id}:{lab_service_id}:{search_text}"
    cached_queue = redis.get(cache_key)
    if cached_queue and refresh == 0:
        return json.loads(cached_queue) if isinstance(cached_queue, str) else json.loads(cached_queue.decode("utf-8"))

    # Fetch from database if not in cache

    db_lab_service_queue = qr.get_lab_service_queue(
        lab_id=lab_id,
        skip=skip,
        limit=limit,
        booking_id=booking_id,
        last_date=last_date,
        start_date=start_date,
        status=status,
        client_id=client_id,
        search_text=search_text,
        lab_service_id=lab_service_id,
    )

    safe_data = jsonable_encoder(db_lab_service_queue)
    redis.set(cache_key, json.dumps(safe_data), ex=300)
    return db_lab_service_queue


@queue_router.put("/{queue_id}", response_model=LabServicesQueueDTO)
def update_lab_service_queue(queue_id: int, lab_service_queue: LabServicesQueueDTO,  qr: QueueRepository = Depends(get_queue_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_lab_service_queue = qr.get_lab_service_queue(queue_id=queue_id)
    if db_lab_service_queue is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return qr.update_lab_service_queue(lab_service_queue=db_lab_service_queue,
                                       new_lab_service_queue=lab_service_queue)


@queue_router.get("/{queue_id}/dynamic-parameters", response_model=List[DynamicParameterDTO])
def get_dynamic_parameters(
    queue_id: int,
    qr: QueueRepository = Depends(get_queue_repository),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    if qr.get_queue(queue_id=queue_id) is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return qr.get_dynamic_parameters(queue_id)


@queue_router.post("/dynamic-parameters", response_model=DynamicParameterDTO)
def create_dynamic_parameter(
    dynamic_parameter: DynamicParameterCreateDTO,
    qr: QueueRepository = Depends(get_queue_repository),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    result = qr.create_dynamic_parameter(dynamic_parameter)
    if result is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return result


@queue_router.put("/{queue_id}/dynamic-parameters", response_model=List[DynamicParameterDTO])
def replace_dynamic_parameters(
    queue_id: int,
    dynamic_parameters: List[DynamicParameterBaseDTO],
    qr: QueueRepository = Depends(get_queue_repository),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    result = qr.replace_dynamic_parameters(queue_id, dynamic_parameters)
    if result is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return result


@queue_router.put("/dynamic-parameters/{dynamic_parameter_id}", response_model=DynamicParameterDTO)
def update_dynamic_parameter(
    dynamic_parameter_id: int,
    dynamic_parameter: DynamicParameterUpdateDTO,
    qr: QueueRepository = Depends(get_queue_repository),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    result = qr.update_dynamic_parameter(dynamic_parameter_id, dynamic_parameter)
    if result is None:
        raise HTTPException(status_code=404, detail="Dynamic parameter not found")
    return result


@queue_router.delete("/dynamic-parameters/{dynamic_parameter_id}")
def delete_dynamic_parameter(
    dynamic_parameter_id: int,
    qr: QueueRepository = Depends(get_queue_repository),
    *,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    if not qr.delete_dynamic_parameter(dynamic_parameter_id):
        raise HTTPException(status_code=404, detail="Dynamic parameter not found")
    return {"deleted": True}


@queue_router.delete("/{queue_id}")
def delete_lab_service_queue(queue_id: int, qr: QueueRepository = Depends(get_queue_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    # delete queue details
    return qr.delete_lab_service_queue(queue_id)


@queue_router.post("/repriotize/")
def repriotize(queue: LabServicesQueueDTO, qr: QueueRepository = Depends(get_queue_repository),*,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    priority_dict = {
        "priority": queue.priority,
        "status": queue.status
    }

    # Get  queuing details
    db_lab_service_queue = qr.update_lab_queue(queue.id, priority_dict)

    # print(queue)
    return 0
