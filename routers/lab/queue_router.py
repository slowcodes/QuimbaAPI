from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from dtos.lab import LabServicesQueueDTO, QueueListingDTO, QueueDTO
from repos.lab.queue_repository import QueueRepository

queue_router = APIRouter(prefix="/api/lab-services-queue", tags=["Lab Services Queue"])


def get_queue_repository(db: Session = Depends(get_db)):
    return QueueRepository(db)


@queue_router.post("/", response_model=LabServicesQueueDTO)
def create_lab_service_queue(queue: LabServicesQueueDTO,
                             qr: QueueRepository = Depends(get_queue_repository)
                             ):
    return qr.create_lab_service_queue(queue)


@queue_router.get("/{queue_id}", response_model=QueueDTO)
def read_lab_service_queue(queue_id: int,  qr: QueueRepository = Depends(get_queue_repository)):
    db_lab_service_queue = qr.get_lab_service_queue(queue_id=queue_id)
    if db_lab_service_queue is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return db_lab_service_queue


@queue_router.get("/", response_model=QueueDTO)
def read_lab_service_queue(lab_id: int = 0, skip: int = 0, limit: int = 10, booking_id: int = 0,
                           search_text: str = '', last_date: str = None,
                           start_date: str = None, status: str = None,  qr: QueueRepository = Depends(get_queue_repository)):
    if search_text != '':
        return qr.search_lab_service_queue(keyword=search_text, skip=skip, limit=limit, lab_id=lab_id)
    else:
        db_lab_service_queue = qr.get_lab_service_queue(lab_id=lab_id, skip=skip,
                                                        limit=limit, booking_id=booking_id,
                                                        last_date=last_date, start_date=start_date,
                                                        status=status)
        if db_lab_service_queue is None:
            raise HTTPException(status_code=404, detail="Lab service queue not found")
        return db_lab_service_queue


@queue_router.put("/{queue_id}", response_model=LabServicesQueueDTO)
def update_lab_service_queue(queue_id: int, lab_service_queue: LabServicesQueueDTO,  qr: QueueRepository = Depends(get_queue_repository)):
    db_lab_service_queue = qr.get_lab_service_queue(db=db, queue_id=queue_id)
    if db_lab_service_queue is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return qr.update_lab_service_queue(db=db, lab_service_queue=db_lab_service_queue,
                                       new_lab_service_queue=lab_service_queue)


@queue_router.delete("/{queue_id}")
def delete_lab_service_queue(queue_id: int, qr: QueueRepository = Depends(get_queue_repository)):
    # delete queue details
    return qr.delete_lab_service_queue(queue_id)


@queue_router.post("/repriotize/")
def repriotize(queue: QueueListingDTO, db: Session = Depends(get_db)):
    qr = QueueRepository(db)

    priority_dict = {
        "priority": queue.priority
    }

    # Get  queuing details
    db_lab_service_queue = qr.update_lab_queue(queue.id, priority_dict)

    # print(queue)
    return 0
