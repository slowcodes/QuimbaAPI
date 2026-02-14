import json
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from twilio.rest import Client

from cache.redis import get_redis_client
from db import get_db
from dtos.auth import UserDTO
from dtos.lab import LabServiceBundleDTO
from dtos.service_dtos.bundles import BundleDTO
from dtos.service_dtos.client_cart_service import ClientServiceCartDTO, ProcessedCartDTO
from dtos.services import ServiceBookingDTO, ServiceBookingDetailDTO
from repos.consultation.consultation_repository import ConsultationsRepository
from repos.lab.queue_repository import QueueRepository
from repos.services.service_bundle_repository import ServiceBundleRepository
from repos.services.service_cart_repository import ServiceCartRepository
from repos.services.service_repository import ServiceRepository
from repos.transaction_repository import TransactionRepository
from security.dependencies import require_access_privilege, get_current_active_user

service_router = APIRouter(prefix="/api/service-bookings", tags=["Service Bookings"])


def service_repository(db: Session = Depends(get_db)):
    return ServiceRepository(db)


def transaction_repository(db: Session = Depends(get_db)):
    return TransactionRepository(db)


def queue_repository(db: Session = Depends(get_db)):
    return QueueRepository(db)


@service_router.post("/", response_model=ServiceBookingDTO, status_code=status.HTTP_201_CREATED)
def create_service_booking(service_booking: ServiceBookingDTO, repo: ServiceRepository = Depends(service_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    booking = repo.create_service_booking(service_booking=service_booking)
    return booking


@service_router.post("/detail/", response_model=ServiceBookingDetailDTO, status_code=status.HTTP_201_CREATED)
def create_service_booking_detail(service_booking_detail: ServiceBookingDetailDTO,
                                  repo: ServiceRepository = Depends(service_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.create_service_booking_detail(service_booking=service_booking_detail)


@service_router.get("/all-booking/", status_code=status.HTTP_200_OK)
def get_service_booking_detail(
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
        skip: int = 0, limit: int = 20, client_id: int = 0, lab_id=0, start_date: str = None, last_date: str = None, status: str = None, booking_type: str = None,
        repo: ServiceRepository = Depends(service_repository)):
    booking = repo.get_all_service_bookings(limit,
                                            skip, client_id, start_date, last_date, status, booking_type, lab_id)
    return booking


@service_router.get("/{service_booking_id}", response_model=ServiceBookingDTO)
def read_service_booking(service_booking_id: int, db: Session = Depends(get_db),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_service_booking = service_repository.get_service_booking(db=db, service_booking_id=service_booking_id)
    if db_service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")
    return db_service_booking


@service_router.put("/{service_booking_id}", response_model=ServiceBookingDTO)
def update_service_booking(service_booking_id: int, service_booking: ServiceBookingDTO,
                           db: Session = Depends(get_db),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_service_booking = service_repository.get_service_booking(db=db, service_booking_id=service_booking_id)
    if db_service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")
    return service_repository.update_service_booking(db=db, service_booking=db_service_booking,
                                                     new_service_booking=service_booking)


@service_router.delete("/{service_booking_id}")
def delete_service_booking(service_booking_id: int,
                           repo: ServiceRepository = Depends(service_repository),
                           transaction_repo: TransactionRepository = Depends(transaction_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
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
                          queue_repo: QueueRepository = Depends(queue_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    service_booking = repo.get_service_booking(service_booking_id)
    if service_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service booking not found")
    return queue_repo.track_booking_from_queue(service_booking_id)


@service_router.get("/service-booking-status/{queue_id}")
def service_booking_status(queue_id: int, repo: ServiceRepository = Depends(service_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.update_transaction_booking_status_based_on_procesed_result(queue_id)


def service_bundle_repository(db: Session = Depends(get_db)):
    return ServiceBundleRepository(db)


@service_router.post("/bundles/", tags=["Service", "Bundles"], status_code=status.HTTP_201_CREATED)
def create_service_bundle(service_bundle: BundleDTO,
                          repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    bundle = repo.add_service_bundle(service_bundle)
    return BundleDTO(**bundle.__dict__)


@service_router.get(
    "/bundles/",
    tags=["Service", "Bundles"],
    summary="Get a list of service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def get_service_bundle(skip: int = 0, limit: int = 20,
                       repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
                       current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
    try:
        # Fetch service bundles from repository
        return repo.get_all_bundles(limit=limit, skip=skip)
    except Exception as e:
        # Log the exception and return an HTTP error response
        raise HTTPException(status_code=500, detail="Failed to retrieve service bundles") from e


@service_router.delete(
    "/bundles/",
    tags=["Service", "Bundles"],
    summary="Delete service bundles",
    description="Delete lab bundles along with collections"
)
def delete_bundle(
        bundle_id: int,
        repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
):
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
                           keyword: str = Query(None, description="Search keyword for bundle name"),
                           repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
                           current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
    try:
        return repo.get_all_bundles(limit, skip, keyword=keyword)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve lab service bundles") from e


@service_router.post(
    "/bundles/laboratory/",
    tags=["Service", "Bundles", "Laboratory"],
    summary="Add laboratory service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def add_lab_service_bundle(lab_service_bundle: BundleDTO,
                           repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
                           current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
    try:
        bundle = repo.add_service_bundle(
            BundleDTO(
                bundles_name=lab_service_bundle.bundles_name,
                bundles_desc=lab_service_bundle.bundles_desc,
                discount=lab_service_bundle.discount,
                bundle_type=lab_service_bundle.bundle_type
            )
        )
        bundle_id = bundle.id
        collections = []

        for bundle_collection in lab_service_bundle.lab_service_bundle:
            bundle_collection.bundles_id = bundle_id
            # del bundle_collection.lab_service_name
            col = repo.add_lab_bundle(bundle_collection)
            collections.append(col)

        return {
            'bundle': bundle,
            'collection': collections
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve lab service bundles") from e


@service_router.put(
    "/bundles/laboratory/",
    tags=["Service", "Bundles", "Laboratory"],
    summary="Add laboratory service bundles",
    description="Retrieve paginated service bundles with optional skip and limit parameters."
)
def add_lab_service_bundle(lab_service_bundle: BundleDTO,
                           repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
                           current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
    try:
        return repo.update_bundle(service_bundle=lab_service_bundle)
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
                                 repo: ServiceBundleRepository = Depends(service_bundle_repository),*, 
                                 current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
    try:
        return repo.delete_lab_bundle(lab_collection_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve lab service bundles") from e


def get_service_cart_repository(db: Session = Depends(get_db)):
    return ServiceCartRepository(db)


@service_router.get(
    "/client/cart/",
    tags=["Service", "Bundles", "Consultation", "Laboratory"],
    summary="Get client saved carts",
    response_model=List[ClientServiceCartDTO],
    description="Retrieve paginated carts item with optional client_id, skip and limit parameters."
)
def get_client_cart_items(client_id: int = Query(..., description="ID of the client"),
                          skip: int = Query(0, ge=0, description="Number of items to skip"),
                          limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return"),
                          start_date: str = Query(None, description="Start date for filtering carts"),
                          last_date: str = Query(None, description="End date for filtering carts"),
                          cart_status: str = Query(None, description="Status filter for carts"),
                          refresh: int = Query(0, ge=0, description="Set to 1 to bypass cache"),
                          repo: ServiceCartRepository = Depends(get_service_cart_repository),*, 
                          current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    try:
        redis = get_redis_client()
        cache_key = f"clients-cart:{skip}:{limit}:{client_id}:{start_date or ''}:{last_date or ''}:{cart_status or ''}"
        cached_client_cart = redis.get(cache_key)

        if cached_client_cart and refresh == 0:
            if isinstance(cached_client_cart, bytes):
                cached_client_cart = cached_client_cart.decode("utf-8")
            try:
                cart = json.loads(cached_client_cart)
            except (TypeError, ValueError):
                cart = cached_client_cart
            return JSONResponse(status_code=status.HTTP_200_OK, content=cart)
        data = repo.get_client_carts(
            client_id=client_id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            last_date=last_date,
            cart_status=cart_status,
        )
        safe_data = jsonable_encoder(data)
        redis.set(cache_key, json.dumps(safe_data), ex=300)  # Cache for 5 minutes
        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve client cart items") from e


@service_router.put(
    "/client/cart/status/",
    tags=["Service", "Consultation", "Laboratory"],
    summary="Update client saved cart",
    response_model=ProcessedCartDTO | None,
    description="Update a client's saved cart status by cart ID.")
def process_client_cart(cart: ProcessedCartDTO,
                        repo: ServiceCartRepository = Depends(get_service_cart_repository),*, 
                        current_user: Annotated[UserDTO, Depends(get_current_active_user)]):
    return repo.update_cart_status(cart)
