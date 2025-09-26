from collections import defaultdict
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from dtos.auth import UserDTO
from dtos.lab import SampleResultDTO, VerifiedResultEntryDTO, DateFilterDTO, LabResultLogCreate
from models.client import Person, Client
from models.lab.lab import SampleResult, LabVerifiedResult, QueueStatus, ResultStatus, LabResultLog, CollectedSamples, \
    LabServicesQueue, LabService
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
        self.queue_repository = QueueRepository(self.db_session)
        self.referral_repository = ReferralRepository(self.db_session)

    def create_result(self, sample_result: SampleResultDTO) -> SampleResultDTO:
        result = SampleResult(sample_id=sample_result.sample_id,
                              created_by=sample_result.created_by,
                              comment=sample_result.comment)
        self.db_session.add(result)
        self.db_session.commit()
        return {
            'id': result.id,
            'sample_id': result.sample_id,
            'comment': result.comment,
            'created_at': result.created_at,
            'created_by': result.created_by
        }

    def delete_result(self, sample_result_id: int) -> bool:
        result = self.get_result_by_id(sample_result_id)

        if result is not None:

            # delete experiment reading
            errr = ExperimentRepository(self.db_session)
            errr.delete_experiment_reading_sample_id(result.sample_id)

            # update sample status to processing
            csr = CollectedSamplesRepository(self.db_session)
            csr.update_processed_sample(result.sample_id, QueueStatus.Processing)

            sample_result = self.db_session.query(SampleResult).filter(SampleResult.id == sample_result_id).first()
            self.db_session.delete(sample_result)
            self.db_session.commit()
            return True

        else:
            return False

    def sample_result_exist(self, sample_result: SampleResultDTO) -> bool:
        exist = self.db_session.query(SampleResult).filter(SampleResult.sample_id == sample_result.sample_id).first()

        if exist:
            return True

        return False

    def get_result_by_id(self, result_id: int) -> SampleResultDTO:
        res = self.db_session.query(SampleResult).filter(SampleResult.id == result_id).first()

        if res:
            return SampleResultDTO(
                id=res.id,
                sample_id=res.sample_id,
                comment=res.comment,
                created_at=res.created_at,
                created_by=res.created_by
            )
        return None

    # def get_result_by_sample_id(self, sample_id: int) -> SampleResultDTO:
    #     res = self.db_session.query(SampleResult).filter(SampleResult.id == sample_id).first()
    #
    #     experiment_repository = ExperimentResultReadingRepository(self.db_session)
    #     return SampleResultDTO(id=res.id,
    #                            sample_id=res.sample_id,
    #                            comment=res.comment,
    #                            created_at=res.created_at,
    #                            created_by=res.created_by,
    #                            experiment_readings=experiment_repository.get_reading_by_sample_id(res.sample_id))

    def get_all_sample_results(self, limit: int, skip: int, lab_id=0, search_keyword: str = '',
                               dateFilter: DateFilterDTO = None) -> dict:
        cols = [
            SampleResult.id,
            SampleResult.sample_id,
            SampleResult.created_at,
            SampleResult.created_by,
            SampleResult.comment,

            CollectedSamples.id.label("sample_id"),
            CollectedSamples.sample_type,
            CollectedSamples.collected_at,
            CollectedSamples.container_label,
            CollectedSamples.collected_by,
            CollectedSamples.queue_id,

            Person.first_name.label('client_first_name'),
            Person.last_name.label('client_last_name'),

            LabServicesQueue.id.label("queue_id"),
            LabServicesQueue.status,
            LabServicesQueue.lab_service_id,
            LabServicesQueue.priority,
            LabServicesQueue.scheduled_at.label("queue_booked_at"), LabService.lab_service_name,

            LabService.lab_id,
            LabService.lab_service_name,

            ServiceBooking.id.label("booking_id"),
        ]

        # initialize base query
        base_query = None

        if dateFilter['status'] == "Verified":
            base_query = self.db_session.query(*cols).select_from(LabVerifiedResult) \
                .join(SampleResult, SampleResult.id == LabVerifiedResult.result_id) \
                .join(CollectedSamples, CollectedSamples.id == SampleResult.sample_id)

        elif dateFilter['status'] == "Not Verified":
            # Entirely written by AI
            base_query = self.db_session.query(*cols).select_from(SampleResult) \
                .join(CollectedSamples, CollectedSamples.id == SampleResult.sample_id) \
                .filter(SampleResult.id.notin_(self.db_session.query(LabVerifiedResult.result_id)))
        else:
            base_query = self.db_session.query(*cols).select_from(SampleResult) \
                .join(CollectedSamples, CollectedSamples.id == SampleResult.sample_id)

        res = base_query.join(LabServicesQueue, LabServicesQueue.id == CollectedSamples.queue_id) \
            .join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .join(Client, Client.id == ServiceBooking.client_id) \
            .join(Person, Person.id == Client.person_id) \
            .join(LabService, LabService.service_id == ServiceBookingDetail.service_id)

        if lab_id != 0:
            res = res.filter(LabService.lab_id == lab_id)

        if search_keyword:
            res = res.filter(Person.first_name.ilike(f'%{search_keyword}%') |
                             Person.last_name.ilike(f'%{search_keyword}%') |
                             LabService.lab_service_name.ilike(f'%{search_keyword}%'))

        if dateFilter:
            if dateFilter['start_date']:
                res = res.filter(SampleResult.created_at >= dateFilter['start_date'])
            if dateFilter['last_date']:
                res = res.filter(SampleResult.created_at <= dateFilter['last_date'])

        total = res.count()
        res = res.limit(limit).offset(skip).all()

        response = []

        for r in res:
            sample_info = self.queue_repository.get_collected_sample_by_queue_id(r.queue_id)
            user = self.user_repository.get_user_by_id(r.created_by)
            response.append(
                {
                    'id': r.id,
                    'booking_id': r.booking_id,
                    'sample': sample_info,  # has results
                    'investigation': r.lab_service_name,
                    'sample_id': r.sample_id,
                    'comment': r.comment,
                    'client_first_name': r.client_first_name,
                    'client_last_name': r.client_last_name,
                    'created_at': r.created_at,
                    'created_by': self.user_repository.get_user(user.username),
                }
            )
        return {
            'data': response,
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

    def get_collated_result(self, limit, skip, lab_id,
                            booking_status: BookingStatus, search_text: str,
                            client_id: int, date_filter: DateFilterDTO, booking_id: int = 0):

        trp = TransactionRepository(self.db_session)
        rs = trp.get_transactions(limit, skip, lab_id,
                                  booking_status, search_text,
                                  TransactionType.All, client_id, date_filter, booking_id)
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
        cols = [
            Transaction.id,
            Transaction.transaction_time,
            ServiceBooking.booking_status,
            Person.last_name,
            Person.first_name,
            Client.id.label("client_id"),
            ServiceBooking.booking_status,
            ServiceBooking.id.label("booking_id")
        ]

        rs = self.db_session.query(*cols).select_from(ServiceBooking) \
            .join(Transaction, Transaction.id == ServiceBooking.transaction_id) \
            .join(Client, Client.id == ServiceBooking.client_id) \
            .join(Person, Person.id == Client.person_id) \
            .filter(ServiceBooking.id == booking_id).first()

        queue_repository = QueueRepository(self.db_session)

        if rs:
            queue_elements = queue_repository.get_lab_service_queue_by_booking_id(booking_id)
            client_repo = ClientRepository(self.db_session)
            approval = ApprovedLabBookingResultRepository(self.db_session)
            return {
                'transaction_id': rs.id,
                'transaction_time': rs.transaction_time,
                'status': rs.booking_status,
                'client': client_repo.get_client(rs.client_id),
                'booking_id': rs.booking_id,
                'booking_completion_status': self.service_repository.get_booking_completion_status(booking_id),
                'queue': queue_elements,
                'approval': approval.get_by_booking_id(booking_id),
                'archived_log': LabResultLogRepository(self.db_session).get_by_booking_id(booking_id,
                                                                                          ResultStatus.Archived),
                'referral': self.referral_repository.get_referred_transaction_referral(rs.id)
            }
        return None

    def verify_result(self, verified_result_entry: VerifiedResultEntryDTO,
                      loggedInUser: UserDTO) -> VerifiedResultEntryDTO:

        verified_result_entry.verified_by = loggedInUser.id
        new_verified_result_entry = LabVerifiedResult(**verified_result_entry.__dict__)
        self.db_session.add(new_verified_result_entry)
        self.db_session.commit()
        self.db_session.refresh(new_verified_result_entry)

        # get all other results associated to this booking ID
        sample_id = self.get_result_by_id(verified_result_entry.result_id).sample_id
        csr = CollectedSamplesRepository(self.db_session)
        collected_sample = csr.get_sample_by_id(sample_id)

        qr = QueueRepository(self.db_session)
        queue = qr.get_queue(collected_sample.queue_id)

        result = self.get_result_by_booking_id(queue.booking_id)

        all_verified: bool = True
        for queue_element in result['queue']:
            for smpl in queue_element.sample:
                if smpl.sample_result.verification:
                    all_verified = False

        if all_verified:
            # update booking status to All  Verified
            self.service_repository.update_booking_status(queue.booking_id, BookingStatus.Verified)

        return new_verified_result_entry

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
