from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from twilio.rest import Client

from db import get_db
from dtos.auth import UserDTO
from dtos.consultation import ConsultationDTO, ConsultationCreate, ConsultationUpdate
from dtos.services import ServiceBookingDTO, ServiceBookingDetailDTO, ServiceBundleDTO, LabServiceBundleDTO
from repos.consultation.consultation_repository import ConsultationsRepository
from repos.lab.queue_repository import QueueRepository
from repos.services.service_bundle_repository import ServiceBundleRepository
from repos.services.service_repository import ServiceRepository
from repos.transaction_repository import TransactionRepository
from security.dependencies import require_access_privilege

service_router = APIRouter(prefix="/api/service-bookings", tags=["Service Bookings"])


def service_repository(db: Session = Depends(get_db)):
    return ServiceRepository(db)


def transaction_repository(db: Session = Depends(get_db)):
    return TransactionRepository(db)


def queue_repository(db: Session = Depends(get_db)):
    return QueueRepository(db)


@service_router.post("/", response_model=ServiceBookingDTO, status_code=status.HTTP_201_CREATED)
def create_service_booking(service_booking: ServiceBookingDTO, repo: ServiceRepository = Depends(service_repository)):
    booking = repo.create_service_booking(service_booking=service_booking)
    return booking


@service_router.post("/detail/", response_model=ServiceBookingDetailDTO, status_code=status.HTTP_201_CREATED)
def create_service_booking_detail(service_booking_detail: ServiceBookingDetailDTO,
                                  repo: ServiceRepository = Depends(service_repository)):
    return repo.create_service_booking_detail(service_booking=service_booking_detail)


@service_router.get("/all-booking/", status_code=status.HTTP_200_OK)
def get_service_booking_detail(
        # current_user: Annotated[UserDTO, Depends(get_current_active_user)],
        skip: int = 0, limit: int = 20, client_id: int = 0, lab_id=0,
        repo: ServiceRepository = Depends(service_repository)):
    booking = repo.get_all_service_bookings(limit,
                                            skip, client_id)
    return booking


@service_router.get("/{service_booking_id}", response_model=ServiceBookingDTO)
def read_service_booking(service_booking_id: int, db: Session = Depends(get_db)):
    db_service_booking = service_repository.get_service_booking(db=db, service_booking_id=service_booking_id)
    if db_service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")
    return db_service_booking


@service_router.put("/{service_booking_id}", response_model=ServiceBookingDTO)
def update_service_booking(service_booking_id: int, service_booking: ServiceBookingDTO,
                           db: Session = Depends(get_db)):
    db_service_booking = service_repository.get_service_booking(db=db, service_booking_id=service_booking_id)
    if db_service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")
    return service_repository.update_service_booking(db=db, service_booking=db_service_booking,
                                                     new_service_booking=service_booking)


@service_router.delete("/{service_booking_id}")
def delete_service_booking(service_booking_id: int,
                           repo: ServiceRepository = Depends(service_repository),
                           transaction_repo: TransactionRepository = Depends(transaction_repository)):
    service_booking = repo.get_service_booking(service_booking_id)

    if service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")

    is_deleted = repo.delete_service_booking_by_id(service_booking)
    if is_deleted['delete']:
        transaction_repo.delete_transaction(service_booking.transaction_id)
        return is_deleted
    return {"delete": False, "msg": is_deleted['msg']}


@service_router.get("/track/{service_booking_id}")
def track_service_booking(service_booking_id: int,
                          repo: ServiceRepository = Depends(service_repository),
                          queue_repo: QueueRepository = Depends(queue_repository)):
    service_booking = repo.get_service_booking(service_booking_id)
    if service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")
    return queue_repo.track_booking_from_queue(service_booking_id)


@service_router.get("/service-booking-status/{sample_id}")
def service_booking_status(sample_id: int, db: Session = Depends(get_db)):
    return service_repository.update_transaction_booking_status_based_on_sample_update(db, sample_id)


def service_bundle_repository(db: Session = Depends(get_db)):
    return ServiceBundleRepository(db)


@service_router.post("/bundles/", tags=["Service", "Bundles"], status_code=status.HTTP_201_CREATED)
def create_service_bundle(service_bundle: ServiceBundleDTO,
                          repo: ServiceBundleRepository = Depends(service_bundle_repository)):
    bundle = repo.add_service_bundle(service_bundle)
    return ServiceBundleDTO(**bundle.__dict__)


@service_router.get(
    "/bundles/",
    tags=["Service", "Bundles"],
    summary="Get a list of service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def get_service_bundle(skip: int = 0, limit: int = 20,
                       repo: ServiceBundleRepository = Depends(service_bundle_repository)):
    try:
        # Fetch service bundles from repository
        return repo.get_service_bundle(limit=limit, skip=skip)
    except Exception as e:
        # Log the exception and return an HTTP error response
        raise HTTPException(status_code=500, detail="Failed to retrieve service bundles") from e


@service_router.delete(
    "/bundles/",
    tags=["Service", "Bundles"],
    summary="Delete service bundles",
    description="Delete lab bundles along with collections"
)
def delete_bundle(bundle_id: int, repo: ServiceBundleRepository = Depends(service_bundle_repository)):
    try:
        return repo.delete_bundle(bundle_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete service bundles") from e


@service_router.get(
    "/bundles/laboratory/",
    tags=["Service", "Bundles", "Laboratory"],
    summary="Get a list of laboratory service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def get_lab_service_bundle(skip: int = 0, limit: int = 20,
                           repo: ServiceBundleRepository = Depends(service_bundle_repository)):
    try:
        return repo.get_lab_bundles(limit, skip)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve lab service bundles") from e


@service_router.post(
    "/bundles/laboratory/",
    tags=["Service", "Bundles", "Laboratory"],
    summary="Add laboratory service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def add_lab_service_bundle(lab_service_bundle: LabServiceBundleDTO,
                           repo: ServiceBundleRepository = Depends(service_bundle_repository)):
    try:
        bundle = repo.add_service_bundle(
            ServiceBundleDTO(
                bundles_name=lab_service_bundle.bundles_name,
                bundles_desc=lab_service_bundle.bundles_desc,
                discount=lab_service_bundle.discount,
                bundle_type=lab_service_bundle.bundle_type
            )
        )
        bundle_id = bundle.id
        collections = []

        for bundle_collection in lab_service_bundle.collections:
            bundle_collection.bundles_id = bundle_id
            del bundle_collection.lab_service_name
            col = repo.add_lab_bundle(bundle_collection)
            collections.append(col)

        return {
            'bundle': bundle,
            'collection': collections
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve lab service bundles") from e


@service_router.delete(
    "/bundles/laboratory/",
    tags=["Service", "Bundles", "Laboratory"],
    summary="Delete laboratory service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def delete_lab_bundle_collection(lab_collection_id: int,
                                 repo: ServiceBundleRepository = Depends(service_bundle_repository)):
    try:
        return repo.delete_lab_bundle(lab_collection_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve lab service bundles") from e



