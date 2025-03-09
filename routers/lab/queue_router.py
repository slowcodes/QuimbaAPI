from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from commands.lab import LabServicesQueueDTO, QueueListingDTO, QueueDTO
from repos.lab.queue_repository import QueueRepository


queue_router = APIRouter(prefix="/api/lab-services-queue", tags=["Lab Services Queue"])


@queue_router.post("/", response_model=LabServicesQueueDTO)
def create_lab_service_queue(queue: LabServicesQueueDTO,
                             db: Session = Depends(get_db)):
    qr = QueueRepository(db)
    return qr.create_lab_service_queue(queue)


@queue_router.get("/{queue_id}", response_model=QueueDTO)
def read_lab_service_queue(queue_id: int, db: Session = Depends(get_db)):
    qr = QueueRepository(db)
    db_lab_service_queue = qr.get_lab_service_queue(queue_id=queue_id)
    if db_lab_service_queue is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return db_lab_service_queue


@queue_router.get("/", response_model=QueueDTO)
def read_lab_service_queue(lad_id: int = 0, skip: int = 0, limit: int = 10, booking_id:int = 0,
                           search_text: str = '', db: Session = Depends(get_db),):
    qr = QueueRepository(db)
    if search_text != '':
        return qr.search_lab_service_queue(keyword=search_text, skip=skip, limit=limit, lab_id=lad_id)
    else:
        db_lab_service_queue = qr.get_lab_service_queue(lab_id=lad_id, skip=skip,
                                                        limit=limit, booking_id=booking_id)
        if db_lab_service_queue is None:
            raise HTTPException(status_code=404, detail="Lab service queue not found")
        return db_lab_service_queue


@queue_router.put("/{queue_id}", response_model=LabServicesQueueDTO)
def update_lab_service_queue(queue_id: int, lab_service_queue: LabServicesQueueDTO, db: Session = Depends(get_db)):
    qr = QueueRepository(db)
    db_lab_service_queue = qr.get_lab_service_queue(db=db, queue_id=queue_id)
    if db_lab_service_queue is None:
        raise HTTPException(status_code=404, detail="Lab service queue not found")
    return qr.update_lab_service_queue(db=db, lab_service_queue=db_lab_service_queue,
                                                     new_lab_service_queue=lab_service_queue)


@queue_router.delete("/{queue_id}")
def delete_lab_service_queue(queue_id: int, db: Session = Depends(get_db)):
    qr = QueueRepository(db)

    # delete queue details
    return qr.delete_lab_service_queue(queue_id)
    # raise HTTPException(status_code=404, detail="Lab service queue not found")


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