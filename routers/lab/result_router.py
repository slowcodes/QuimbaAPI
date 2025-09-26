from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from dtos.auth import UserDTO
from dtos.lab import ExperimentResultReadingDTO, SampleResultDTO, VerifiedResultEntryDTO, DateFilterDTO, \
    ApprovedLabBookingResultDTO
from dtos.services import ServiceBookingDTO
from db import get_db
from models.services.services import BookingStatus
from repos.lab.experiment_repository import ExperimentRepository
from repos.lab.result.approved_lab_booking_result import ApprovedLabBookingResultRepository
from repos.lab.result_repository import ResultRepository
from repos.lab.sample_repository import CollectedSamplesRepository
from repos.transaction_repository import TransactionRepository
from security.dependencies import get_current_active_user

result_router = APIRouter(prefix="/api/lab-results", tags=["Lab Results"])


def experiment_result_repo(db: Session = Depends(get_db)) -> ExperimentRepository:
    return ExperimentRepository(db)


def transaction_repo(db: Session = Depends(get_db)) -> TransactionRepository:
    return TransactionRepository(db)


@result_router.post("/experiment-results/", response_model=ExperimentResultReadingDTO)
def create_experiment_result(reading: ExperimentResultReadingDTO,
                             repo: ExperimentRepository = Depends(experiment_result_repo)):
    if repo.reading_exits(reading):
        raise HTTPException(status_code=409, detail="Experiment reading already exist")
    return repo.create_reading(reading)


@result_router.get("/experiment-results/{reading_id}")
def read_experiment_result(reading_id: int, repo: ExperimentRepository = Depends(experiment_result_repo)):
    db_reading = repo.get_reading_by_id(reading_id)
    if db_reading is None:
        raise HTTPException(status_code=404, detail="Experiment reading not found")
    return db_reading


def sample_result_repo(db: Session = Depends(get_db)) -> ResultRepository:
    return ResultRepository(db)


@result_router.post("/sample-results/")
def create_sample_result(result: SampleResultDTO,
                         current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                         repo: ResultRepository = Depends(sample_result_repo),
                         db: Session = Depends(get_db),
                         ):
    result.created_by = current_user.id
    if repo.sample_result_exist(result):
        raise HTTPException(status_code=409, detail="Sample result already exist")
    response = repo.create_result(result)

    # update sample status to processed
    collected_sample_repo = CollectedSamplesRepository(db)
    collected_sample_repo.update_processed_sample(result.sample_id)
    return response


@result_router.get("/sample-results/")
def read_sample_results(limit: int = 15, skip: int = 0,
                        lab_id: int = 0, search_text: Optional[str] = None,
                        start_date: Optional[str] = None,
                        last_date: Optional[datetime] = None,
                        date_filter_status: Optional[str] = None,
                        repo: ResultRepository = Depends(sample_result_repo)):
    date_filter: DateFilterDTO = {
        "start_date": start_date,
        "last_date": last_date,
        "status": date_filter_status
    }
    sample_results = repo.get_all_sample_results(limit, skip, lab_id, search_text, date_filter)

    if sample_results is None:
        raise HTTPException(status_code=404, detail="No results found")
    return sample_results


@result_router.get("/sample-results/verified/")
def read_verified_sample_results(limit: int = 15, skip: int = 0, lab_id: int = 0, search_text: str = '',
                                 start_date: datetime = None, last_date: datetime = None, date_filter_status: str = '',
                                 repo: ResultRepository = Depends(sample_result_repo)):
    date_filter: DateFilterDTO = {
        "start_date": start_date,
        "last_date": last_date,
        "status": date_filter_status
    }

    verified_sample_results = repo.get_all_verified_sample_results(
        limit, skip, lab_id, search_text, date_filter)

    if verified_sample_results is None:
        raise HTTPException(status_code=404, detail="No results found")
    return verified_sample_results


@result_router.delete("/sample-results/{result_id}")
def delete_sample_result(result_id: int,
                         repo: ResultRepository = Depends(sample_result_repo)):
    response = repo.delete_result(sample_result_id=result_id)
    if not response:
        raise HTTPException(status_code=409, detail="Sample result does not exist")
    return {
        'data': response,
        'msg': "Result has been successfully deleted"
    }


@result_router.get("/sample-results/{result_id}", response_model=SampleResultDTO)
def read_sample_result(result_id: int, repo: ResultRepository = Depends(sample_result_repo)):
    db_result = repo.get_result_by_id(result_id)
    if db_result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return db_result


@result_router.get("/sample-results/collated-results/")
def read_collated_results(limit: int = 15, skip: int = 0, booking_status: BookingStatus = BookingStatus.Processing,
                          lab_id: int = 0, search_text: str = '', client_id: int = 0,
                          start_date: datetime = None, last_date: datetime = None, date_filter_status: str = '',
                          booking_id: int = 0,
                          repo: ResultRepository = Depends(sample_result_repo)):
    date_filter: DateFilterDTO = {
        "start_date": start_date,
        "last_date": last_date,
        "status": date_filter_status
    }

    results = repo.get_collated_result(limit, skip, lab_id,
                                       booking_status, search_text,
                                       client_id, date_filter, booking_id)
    if results is None:
        raise HTTPException(status_code=404, detail="No results found")
    return results


@result_router.get("/booking-result/")
def read_group_booking_result(booking_id: int,
                              repo: ResultRepository = Depends(sample_result_repo)):
    result = repo.get_result_by_booking_id(booking_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@result_router.post("/sample-results/verify-result")
def create_result_verification(verified_result_entry: VerifiedResultEntryDTO,
                               current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                               repo: ResultRepository = Depends(sample_result_repo),
                               ):
    db_result = repo.get_result_by_id(verified_result_entry.result_id)
    if db_result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return repo.verify_result(verified_result_entry, current_user)


@result_router.get("/")
def read_collated_results(limit: int = 15, skip: int = 0, booking_status: BookingStatus = BookingStatus.Processing,
                          lab_id: int = 0, search_text: str = '', client_id: int = 0,
                          start_date: str = '', last_date: str = '', date_filter_status: str = '',
                          repo: TransactionRepository = Depends(transaction_repo)):
    date_filter: DateFilterDTO = {
        "start_date": start_date,
        "last_date": last_date,
        "status": date_filter_status
    }

    results = repo.get_laboratory_transaction_details(limit, skip, lab_id, booking_status, search_text, client_id,
                                                      date_filter)

    if results is None:
        raise HTTPException(status_code=204, detail="No content found")
    return results


@result_router.post("/archive")
def archive_completed_lab_booking(booking: ServiceBookingDTO,
                                  current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                                  repo: ResultRepository = Depends(sample_result_repo)):
    state = repo.archive_result(booking.id, current_user)

    # log = repo.log_booking_result(booking.id, ResultStatus.Archived)

    if state is None:
        raise HTTPException(status_code=204, detail="No content found")
    return


@result_router.delete("/unarchive")
def unarchive_completed_lab_booking(booking_id: int,
                                    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                                    repo: ResultRepository = Depends(sample_result_repo)):
    state = repo.unarchive_result(booking_id)

    if state is False:
        raise HTTPException(status_code=204, detail="No content found")
    return


@result_router.get("/analytics/compute-average-times")
def compute_average_times(lab_service_id: int = 0, lab_id: int = 0, start_date: str = None,
                          last_date: str = None, date_filter_status: str = None,
                          repo: ResultRepository = Depends(sample_result_repo)):
    # try:
    date_filter: DateFilterDTO = {
        "start_date": start_date,
        "last_date": last_date,
        "status": date_filter_status
    }
    average_times = repo.compute_avg_processing_time(lab_service_id, lab_id, date_filter)
    return average_times


# except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))


@result_router.get("/analytics/generate-barchart-data")
def generate_barchart_data(start_date: str = None, last_date: str = None,
                           interval: str = 'daily', lab_id: int = 0,
                           repo: ResultRepository = Depends(sample_result_repo)):
    try:
        data = repo.generate_barchart_data(start_date, last_date, interval.lower(), lab_id)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@result_router.get("/analytics/total-bookings-per-lab-service")
def get_total_bookings_per_lab_service(start_date: str = None, end_date: str = None, lab_id: int = 0,
                                       lab_service_id: int = 0,
                                       repo: ResultRepository = Depends(sample_result_repo)):
    try:
        data = repo.get_total_bookings_per_lab_service()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_approved_result_repository(db: Session = Depends(get_db)):
    return ApprovedLabBookingResultRepository(db)


@result_router.get("/approved-booking-results/{id}", response_model=ApprovedLabBookingResultDTO)
def get_approved_lab_booking_result(id: int, repository: ApprovedLabBookingResultRepository = Depends(
    get_approved_result_repository)):
    result = repository.get_by_id(id)
    if result is None:
        raise HTTPException(status_code=404, detail="ApprovedLabBookingResult not found")
    return result


@result_router.get("/approved_lab_booking_results/booking/{booking_id}", response_model=ApprovedLabBookingResultDTO)
def get_approved_lab_booking_result_by_booking_id(booking_id: int,
                                                  repository: ApprovedLabBookingResultRepository = Depends(
                                                      get_approved_result_repository)):
    result = repository.get_by_booking_id(booking_id)

    if result is None:
        raise HTTPException(status_code=404, detail="ApprovedLabBookingResult not found")
    return result


@result_router.post("/approved_lab_booking_results", response_model=ApprovedLabBookingResultDTO)
def create_approved_lab_booking_result(dto: ApprovedLabBookingResultDTO,
                                       current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                                       repo: ApprovedLabBookingResultRepository = Depends(
                                           get_approved_result_repository)):
    result = repo.create(dto, current_user)
    if result is None:
        raise HTTPException(status_code=400, detail="Error creating ApprovedLabBookingResult")
    return result


@result_router.put("/approved_lab_booking_results/{id}", response_model=ApprovedLabBookingResultDTO)
def update_approved_lab_booking_result(id: int, dto: ApprovedLabBookingResultDTO,
                                       repository: ApprovedLabBookingResultRepository = Depends(
                                           get_approved_result_repository)):
    result = repository.update(id, dto)
    if result is None:
        raise HTTPException(status_code=404, detail="ApprovedLabBookingResult not found")
    return result


@result_router.delete("/approved_lab_booking_results/{id}", response_model=bool)
def delete_approved_lab_booking_result(id: int,
                                       repository: ApprovedLabBookingResultRepository = Depends(
                                           get_approved_result_repository)):
    result = repository.delete_by_booking_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="ApprovedLabBookingResult not found")
    return result
