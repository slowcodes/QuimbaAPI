import traceback
from collections import defaultdict
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from dtos.auth import UserDTO
from dtos.lab import SampleResultDTO, VerifiedResultEntryDTO, DateFilterDTO, LabResultLogCreate
from models.client import Person, Client
from models.lab.lab import SampleResult, LabVerifiedResult, QueueStatus, ResultStatus, LabResultLog, CollectedSamples, \
    LabServicesQueue, LabService, LabType
from models.services.services import ServiceBooking, BookingStatus, ServiceBookingDetail, BusinessServices
from models.transaction import Transaction, TransactionType
from repos.auth_repository import UserRepository
from repos.client.client_repository import ClientRepository
from repos.client.referral_repository import ReferralRepository
from repos.lab.experiment_repository import ExperimentRepository
from repos.lab.queue_repository import QueueRepository
from repos.lab.result.approved_lab_booking_result import ApprovedLabBookingResultRepository
from repos.lab.result.lab_result_log_repository import LabResultLogRepository
from repos.lab.sample_repository import CollectedSamplesRepository
from repos.services.service_repository import ServiceRepository
from repos.transaction_repository import TransactionRepository


class ResultRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.user_repository = UserRepository(self.db_session)
        self.experiment_repository = ExperimentRepository(self.db_session)
        self.service_repository = ServiceRepository(self.db_session)
        # self.queue_repository = QueueRepository(self.db_session)
        self.referral_repository = ReferralRepository(self.db_session)
        self.collected_sample_repository = CollectedSamplesRepository(self.db_session)
        self.transaction_repository = TransactionRepository(self.db_session)

    def create_result(self, sample_result: SampleResultDTO) -> SampleResultDTO:
        result = SampleResult(queue_id=sample_result.queue_id,
                              created_by=sample_result.created_by,
                              comment=sample_result.comment)
        self.db_session.add(result)

        # update collected sample as processed
        self.collected_sample_repository.update_processed_sample(
            result.queue_id
        )

        # update queue status as processed
        self.queue_repository.update_lab_queue(result.queue_id, {'status': QueueStatus.Processed})

        self.db_session.commit()
        return {
            'id': result.id,
            'queue_id': result.queue_id,
            'comment': result.comment,
            'created_at': result.created_at,
            'created_by': result.created_by
        }

    def delete_result(self, sample_result_id: int) -> bool:
        try:
            result = self.get_result_by_id(sample_result_id)

            if result is not None:

                # delete experiment reading
                errr = ExperimentRepository(self.db_session)
                errr.delete_experiment_reading_result_id(result.id)

                # delete verification if it exists
                self.db_session.query(LabVerifiedResult).filter(LabVerifiedResult.result_id == result.id).delete()

                if result.queue.lab_service.lab_type == LabType.Observation:
                    # set queue as processing
                    self.queue_repository.update_lab_queue(
                        result.queue_id,
                        {'status': QueueStatus.Processing}
                    )
                else:
                    # update sample status to processing
                    csr = CollectedSamplesRepository(self.db_session)
                    csr.update_processed_sample(result.queue_id, QueueStatus.Processing)

                sample_result = self.db_session.query(SampleResult).filter(SampleResult.id == sample_result_id).first()
                self.db_session.delete(sample_result)
                self.db_session.commit()
                return True

            else:
                return False

        except Exception as e:
            self.db_session.rollback()
            traceback.print_exc()  # ✅ FULL STACK TRACE
            raise  #

    def sample_result_exist(self, sample_result: SampleResultDTO) -> bool:
        exist = self.db_session.query(SampleResult).filter(SampleResult.queue_id == sample_result.queue_id).first()

        if exist:
            return True

        return False

    def get_result_by_id(self, result_id: int) -> SampleResultDTO:
        res = self.db_session.query(SampleResult).filter(SampleResult.id == result_id).first()

        if res:
            return SampleResultDTO.from_orm(res)
        return None

    def get_all_sample_results(self, limit: int, skip: int, lab_id=0, search_keyword: str = '',
                               dateFilter: DateFilterDTO = None, client_id: int = 0) -> dict:

        base_query = self.db_session.query(SampleResult)
        joined_queue = False
        joined_lab_service = False
        status_value = None
        start_date = None
        last_date = None
        if dateFilter:
            status_value = getattr(dateFilter, "status", None)
            start_date = getattr(dateFilter, "start_date", None)
            last_date = getattr(dateFilter, "last_date", None)
            if isinstance(dateFilter, dict):
                status_value = dateFilter.get("status")
                start_date = dateFilter.get("start_date")
                last_date = dateFilter.get("last_date")

        if lab_id != 0:
            base_query = base_query.join(LabServicesQueue, LabServicesQueue.id == SampleResult.queue_id) \
                .join(LabService, LabService.id == LabServicesQueue.lab_service_id).filter(LabService.lab_id == lab_id)
            joined_queue = True
            joined_lab_service = True

        if status_value in ResultStatus.__members__:
            base_query = base_query.filter(LabVerifiedResult.status == status_value)

        if search_keyword or client_id:
            if not joined_queue:
                base_query = base_query.join(LabServicesQueue, LabServicesQueue.id == SampleResult.queue_id)
                joined_queue = True
            if not joined_lab_service:
                base_query = base_query.join(LabService, LabService.id == LabServicesQueue.lab_service_id)
                joined_lab_service = True
            base_query = base_query.join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
                .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
                .join(Client, Client.id == ServiceBooking.client_id)

            if client_id:
                base_query = base_query.filter(ServiceBooking.client_id == client_id)

            if search_keyword:
                base_query = base_query.join(Person, Person.id == Client.person_id) \
                    .filter(Person.first_name.ilike(f'%{search_keyword}%') |
                            Person.last_name.ilike(f'%{search_keyword}%') |
                            LabService.lab_service_name.ilike(f'%{search_keyword}%'))

        if start_date:
            base_query = base_query.filter(SampleResult.created_at >= start_date)
        if last_date:
            base_query = base_query.filter(SampleResult.created_at <= last_date)

        total = base_query.count()
        res = base_query.limit(limit).offset(skip).all()

        return {
            'data': [SampleResultDTO.from_orm(record) for record in res],
            'total': total
        }

    def compute_avg_processing_time(self, lab_service_id: int = 0, lab_id: int = 0, date_filter: DateFilterDTO = None):
        cols = [
            ServiceBookingDetail.booking_id,
            LabServicesQueue.scheduled_at.label("booking_time"),
            CollectedSamples.collected_at,
            ServiceBooking.transaction_id,
            BusinessServices.ext_turn_around_time,
            SampleResult.created_at.label("result_processed_at"),
            LabVerifiedResult.verified_at,
            LabService.lab_service_name
        ]

        rs = self.db_session.query(*cols).select_from(LabServicesQueue) \
            .join(LabService, LabService.id == LabServicesQueue.lab_service_id) \
            .join(BusinessServices, BusinessServices.service_id == LabService.service_id) \
            .join(CollectedSamples, CollectedSamples.queue_id == LabServicesQueue.id) \
            .join(SampleResult, SampleResult.sample_id == CollectedSamples.id) \
            .join(LabVerifiedResult, LabVerifiedResult.result_id == SampleResult.id) \
            .join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            # .filter(LabService.id == lab_service_id).all()

        if lab_id != 0:
            rs = rs.filter(LabService.lab_id == lab_id)

        elif lab_service_id != 0:
            rs = rs.filter(LabService.id == lab_service_id)

        if date_filter:
            start_date = date_filter['start_date']
            last_date = date_filter['last_date']
            status = date_filter['status']

            if start_date:
                rs = rs.filter(LabServicesQueue.scheduled_at >= start_date)
            if last_date:
                rs = rs.filter(LabServicesQueue.scheduled_at <= last_date)

        # ddd approval time
        rs = rs.all()

        total_booking_to_verification = 0
        total_booking_to_collection = 0
        total_booking_to_processing = 0
        count = len(rs)

        if count == 0:
            est_turn_around_time = 0
        else:
            est_turn_around_time = rs[0].ext_turn_around_time

        bookings_completed_before_est_delivery = 0
        bookings_completed_after_est_delivery = 0

        data = []
        for record in rs:
            data.append(
                {
                    'transaction_id': record.transaction_id,
                    'booking_id': record.booking_id,
                    'booking_time': record.booking_time,
                    'collected_at': record.collected_at,
                    'result_processed_at': record.result_processed_at,
                    'verified_at': record.verified_at,
                    'lab_service_name': record.lab_service_name
                }
            )
            booking_time = record.booking_time
            collected_at = record.collected_at
            result_processed_at = record.result_processed_at
            verified_at = record.verified_at

            booking_to_verification = (verified_at - booking_time).total_seconds()
            booking_to_collection = (collected_at - booking_time).total_seconds()
            booking_to_processing = (result_processed_at - booking_time).total_seconds()

            total_booking_to_verification += booking_to_verification
            total_booking_to_collection += booking_to_collection
            total_booking_to_processing += booking_to_processing

            if booking_to_verification <= est_turn_around_time * 60:
                bookings_completed_before_est_delivery += 1
            else:
                bookings_completed_after_est_delivery += 1

        avg_booking_to_verification = (total_booking_to_verification / count / 60) if count else 0
        avg_booking_to_collection = (total_booking_to_collection / count / 60) if count else 0
        avg_booking_to_processing = (total_booking_to_processing / count / 60) if count else 0

        return {
            'data': data,
            'total_number_of_bookings': count,
            'est_turn_around_time': est_turn_around_time,
            'booking_completed_before_est_delivery': bookings_completed_before_est_delivery,
            'booking_completed_after_est_delivery': bookings_completed_after_est_delivery,
            'avg_booking_to_verification': avg_booking_to_verification,
            'avg_booking_to_collection': avg_booking_to_collection,
            'avg_booking_to_processing': avg_booking_to_processing,
            'computed_est_turn_around_time': avg_booking_to_processing + avg_booking_to_collection + avg_booking_to_verification,
        }

    def generate_barchart_data(self, start_date: str,
                               last_date: str, interval: str, lab_id=0, lab_service_id=0):

        if interval not in ['daily', 'weekly', 'monthly']:
            raise ValueError("Interval must be 'daily', 'weekly', or 'monthly'")

        date_format = {
            'daily': '%Y-%m-%d',
            'weekly': '%Y-%W',
            'monthly': '%Y-%m'
        }[interval]

        # Determine the database dialect (SQLite, PostgreSQL, MySQL, etc.)
        dialect = str(self.db_session.bind.dialect)

        # Adjust date formatting function based on database dialect
        if 'sqlite' in dialect:
            date_func = func.strftime(date_format, Transaction.transaction_time)
        elif 'postgresql' in dialect:
            date_func = func.to_char
        else:
            # Default to MySQL's date_format function
            date_func = func.date_format

        rs = self.db_session.query(
            LabService.lab_service_name,
            date_func.label('period'),
            func.count(ServiceBooking.id).label('count')
        ).join(ServiceBookingDetail, ServiceBookingDetail.service_id == LabService.service_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .join(Transaction, Transaction.id == ServiceBooking.transaction_id)

        if lab_id != 0:
            rs = rs.filter(LabService.lab_id == lab_id)

        if lab_service_id != 0:
            rs = rs.filter(LabService.id == lab_service_id)

        if (start_date is not None) and (last_date is not None):
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_dt = datetime.strptime(last_date, '%Y-%m-%d')
            rs = rs.filter(Transaction.transaction_time.between(start_date_dt, end_date_dt)) \
                .group_by('period', LabService.lab_service_name) \
                .order_by('period').all()
        else:
            rs = rs.group_by('period', LabService.lab_service_name) \
                .order_by('period').all()

        data = defaultdict(lambda: defaultdict(int))
        for record in rs:
            data[record.lab_service_name][record.period] = record.count

        return data

    def get_total_bookings_per_lab_service(self):
        rs = self.db_session.query(
            LabService.lab_service_name,
            func.count(ServiceBooking.id).label('total_bookings')
        ).join(ServiceBookingDetail, ServiceBookingDetail.service_id == LabService.service_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .group_by(LabService.lab_service_name) \
            .all()

        return {record.lab_service_name: record.total_bookings for record in rs}

    def get_collated_result_by_queue(self, limit, skip, lab_id,
                                    search_text: str, client_id: int, date_filter: DateFilterDTO):

        trx = self.transaction_repository.get_all_lab(
            client_id=client_id,
            lab_id=lab_id,
            date_filter=date_filter,
            limit=limit,
            skip=skip,
            booking_status=date_filter["status"] if date_filter and "status" in date_filter else None,
            search_text=search_text
        )
        return trx

    def get_collated_result(self, limit, skip, lab_id,
                            booking_status: BookingStatus, search_text: str,
                            client_id: int, date_filter: DateFilterDTO, booking_id: int = 0):

        print("Fetching collated results with parameters:", booking_status)
        trp = TransactionRepository(self.db_session)
        rs = trp.get_all_lab(
            date_filter=date_filter,
            skip=skip,
            limit=limit,
            lab_id=lab_id,
            client_id=client_id,
            booking_status=booking_status
        )
        response = []
        for lab_booking in rs['transactions']:
            # get queue elements
            queue_elements = self.queue_repository.get_lab_service_queue_by_booking_id(lab_booking.booking_id)

            response.append(
                {
                    'transaction_id': lab_booking.id,
                    'transaction_time': lab_booking.transaction_time,
                    'status': lab_booking.booking_status,
                    'client_first_name': lab_booking.first_name,
                    'client_last_name': lab_booking.last_name,
                    'booking_id': lab_booking.booking_id,
                    'booking_completion_status': self.service_repository.get_booking_completion_status(
                        lab_booking.booking_id),
                    'queue': queue_elements,
                    'approval': ApprovedLabBookingResultRepository(self.db_session).get_by_booking_id(
                        lab_booking.booking_id),
                    'archived_log': LabResultLogRepository(self.db_session).get_by_booking_id(lab_booking.booking_id,
                                                                                              ResultStatus.Archived)

                }
            )

        return {
            'data': response,
            'total': rs['total']
        }

    def get_result_by_booking_id(self, booking_id: int):
        res = self.db_session.query(SampleResult) \
            .join(LabServicesQueue, LabServicesQueue.id == SampleResult.queue_id) \
            .join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .filter(ServiceBooking.id == booking_id).all()

        return [SampleResultDTO.from_orm(record) for record in res]

    def verify_result(self, verified_result_entry: VerifiedResultEntryDTO,
                      loggedInUser: UserDTO) -> VerifiedResultEntryDTO:
        verified = LabVerifiedResult(
            result_id=verified_result_entry.result_id,
            verified_by=loggedInUser.id,
            comment=verified_result_entry.comment,
            status=verified_result_entry.status
        )
        self.db_session.add(verified)
        self.db_session.commit()
        self.db_session.refresh(verified)

        # get all other results associated to this booking ID
        res = self.get_result_by_id(verified_result_entry.result_id)
        other_booking_results = self.get_result_by_booking_id(res.queue.booking_id)

        all_verified: bool = True
        for fellow_result in other_booking_results:
            if fellow_result.verification is None:
                all_verified = False

        if all_verified:
            # update booking status to All  Verified
            self.service_repository.update_booking_status(res.queue.booking_id, BookingStatus.Verified)

        return verified

    def archive_result(self, booking_id: int, user: UserDTO):
        LabResultLogRepository(self.db_session).create(LabResultLogCreate(
            booking_id=booking_id,
            logged_by=user.id,
            action=ResultStatus.Archived)
        )
        return self.service_repository.update_booking_status(booking_id,
                                                             BookingStatus.Processed)

    def unarchive_result(self, booking_id: int):
        LabResultLogRepository(self.db_session).delete_by_booking_id(booking_id, ResultStatus.Archived)
        return self.service_repository.update_booking_status(booking_id,
                                                             BookingStatus.Processing)

    def log_booking_result(self, booking_id: int, status: ResultStatus) -> LabResultLog:
        user = UserRepository(self.db_session)
        lab_result_log = LabResultLog(
            logged_by=user.get_logged_in_user_id(),
            booking_id=booking_id,
            action=status
        )
        self.db_session.add(lab_result_log)
        self.db_session.commit()
        self.db_session.refresh(lab_result_log)
        return lab_result_log
