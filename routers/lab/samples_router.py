import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List

from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

from cache.redis import get_redis_client
from dtos.lab import CollectedSamplesDTO, LabServicesQueueDTO
from db import get_db
from models.lab.lab import SampleType, QueueStatus
from repos.lab.queue_repository import QueueRepository
from repos.lab.sample_repository import CollectedSamplesRepository

from fastapi import APIRouter

sample_collection_router = APIRouter(prefix="/api/laboratories/collected-samples", tags=["Sample Collection"])


@sample_collection_router.get("/sample-types")
def get_sample_types():
    sTypes = []
    for sample_type in SampleType.__members__.values():
        sTypes.append(sample_type)
    return sTypes


def get_repository(db: Session = Depends(get_db)) -> CollectedSamplesRepository:
    return CollectedSamplesRepository(db)


@sample_collection_router.get("/single-sample/{sample_id}")
def get_collected_sample(sample_id: int, repo: CollectedSamplesRepository = Depends(get_repository)):
    collected_sample = repo.get_collected_sample_by_id(sample_id)
    return collected_sample


@sample_collection_router.post("/", response_model=CollectedSamplesDTO)
def create_collected_sample(sample_data: CollectedSamplesDTO,
                            repo: CollectedSamplesRepository = Depends(get_repository),
                            db: Session = Depends(get_db)):
    queueRepo = QueueRepository(db)
    queue = queueRepo.get_queue(sample_data.queue_id)

    queueRepo.update_lab_service_queue(
        queueRepo.get_queue(sample_data.queue_id),
        LabServicesQueueDTO(
            id=sample_data.queue_id,
            status=QueueStatus.Processed,
            booking_id=queue.booking_id,
            lab_service_id=queue.lab_service_id
        )
    )
    return repo.add_collected_sample(sample_data)


@sample_collection_router.get("/")  # response_model=List[CollectedSamplesDTO]
def get_collected_samples(skip: int = 0, limit: int = 10, lab_id: int = 0, booking_id: int = 0,
                          start_date: str = None, last_date: str = None, status: QueueStatus = QueueStatus.Processing,
                          search_keyword: str = None, refresh: int = 0, repo: CollectedSamplesRepository = Depends(get_repository)):
    date_filter = {
        'start_date': start_date,
        'last_date': last_date,
        'status': status
    }
    redis = get_redis_client()
    cache_key = f"clients:{skip}:{limit}:{lab_id}:{booking_id}:{start_date}:{last_date}:{status}:{search_keyword}"
    cached_samples = redis.get(cache_key)

    if cached_samples and refresh == 0:
        samples = json.loads(cached_samples.decode("utf-8"))
        return JSONResponse(status_code=HTTP_200_OK, content=samples)

    data = repo.get_collected_samples(skip, limit, lab_id, booking_id, date_filter, search_keyword)
    safe_data = jsonable_encoder(data)
    redis.set(cache_key, json.dumps(safe_data), ex=300)
    return data


@sample_collection_router.put("/{sample_id}")
def update_collected_sample(sample_id: int, sample_data: CollectedSamplesDTO,
                            repo: CollectedSamplesRepository = Depends(get_repository)):
    if not repo.get_collected_sample_by_id(sample_id):
        raise HTTPException(status_code=404, detail="Collected sample not found")
    # Perform update operation using repository method
    # For example:
    # repo.update_collected_sample(sample_id, sample_data)
    return {"message": "Collected sample updated successfully"}


@sample_collection_router.delete("/{sample_id}")
def delete_collected_sample(sample_id: int,
                            repo: CollectedSamplesRepository = Depends(get_repository)):
    if not repo.get_sample_by_id(sample_id):
        raise HTTPException(status_code=400, detail="Collected sample not found")

    # Perform delete operation using repository method
    repo.delete_collected_sample(sample_id)

    return {"message": "Collected sample deleted successfully"}

#
# @sample_collection_router.get("/sample-types")
# def get_sample_types():
#     return []
