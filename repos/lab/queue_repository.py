from typing import List

from sqlalchemy.orm import Session

from dtos.lab import LabServicesQueueDTO, QueueDTO, VerifiedResultEntryDTO
from dtos.services import ServiceEventDTO, EventType, ServiceTrackingDTO
from models.client import Client, Person
from models.lab.lab import LabServicesQueue, Laboratory, QueueStatus, LabService, CollectedSamples, SampleResult, \
    LabVerifiedResult
from models.services import ServiceBooking, BusinessServices, ServiceBookingDetail
from repos.auth_repository import UserRepository
from repos.lab.experiment_repository import ExperimentRepository
from repos.services.service_repository import ServiceRepository
from repos.transaction_repository import TransactionRepository


class QueueRepository:

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.cols = [LabServicesQueue.id.label('id'),
                     LabServicesQueue.scheduled_at.label('scheduled_at'),
                     LabServicesQueue.status.label('status'),
                     ServiceBooking.id.label('booking_id'),
                     LabServicesQueue.priority.label('priority'),
                     Laboratory.lab_name.label('laboratory'),
                     LabService.lab_service_name.label('lab_service_name'),
                     BusinessServices.ext_turn_around_time.label('ext_turn_around_time'),
                     Person.first_name.label('client_first_name'),
                     Person.last_name.label('client_last_name')
                     ]
        self.base_query = self.db_session.query(*self.cols) \
            .select_from(LabServicesQueue). \
            join(LabService, LabServicesQueue.lab_service_id == LabService.id). \
            join(Laboratory, Laboratory.id == LabService.lab_id). \
            join(BusinessServices, BusinessServices.service_id == LabService.service_id). \
            join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id). \
            join(ServiceBooking, ServiceBookingDetail.booking_id == ServiceBooking.id). \
            join(Client, Client.id == ServiceBooking.client_id). \
            join(Person, Person.id == Client.person_id)

        self.transaction_repository = TransactionRepository(self.db_session)
        self.user_repository = UserRepository(self.db_session)

    def create_lab_service_queue(self, lab_service_queue_dto: LabServicesQueueDTO) -> LabServicesQueueDTO:
        lab_service_queue = LabServicesQueue(**lab_service_queue_dto.dict())
        self.db_session.add(lab_service_queue)
        self.db_session.commit()
        self.db_session.refresh(lab_service_queue)
        queue = {
            'id': lab_service_queue.id,
            'lab_service_id': lab_service_queue.lab_service_id,
            'scheduled_at': lab_service_queue.scheduled_at,
            'status': lab_service_queue.status,
            'priority': lab_service_queue.priority,
            'booking_id': lab_service_queue.booking_id
        }
        return queue

    def search_lab_service_queue(self, keyword='', skip=0, limit=10, lab_id: int = 0) -> QueueDTO:
        query = self.base_query. \
            filter(LabService.lab_service_name.ilike(f"%{keyword}%")
                   | Laboratory.lab_name.ilike(f"%{keyword}%")
                   | Client.first_name.ilike(f"%{keyword}")
                   | Client.last_name.ilike(f"%{keyword}")
                   | Client.date_of_birth.ilike(f"%{keyword}")
                   | LabService.lab_service_name.ilike(f"%{keyword}"))

        if lab_id != 0:
            query = query.filter(Laboratory.id == lab_id)

        count = query.count()
        query = query.offset(skip).limit(limit)
        results = query.all()
        return {
            'queue': self.generate_queue_list(results),
            'total': count
        }

    def get_lab_service_queue(self, lab_id: int = 0, skip: int = 0,
                              limit: int = 10, booking_id: int = 0,
                              last_date: str = None, start_date: str = None, status: str = None) -> QueueDTO:

        query = self.base_query
        if lab_id != 0:
            query = query.filter(Laboratory.id == lab_id)

        if booking_id != 0:
            query = query.filter(ServiceBookingDetail.booking_id == booking_id)

        if last_date is not None and start_date is not None:
            last_date = last_date + " 23:59:59.000001"
            start_date = start_date + " 00:00:00.000001"
            query = query.filter(
                LabServicesQueue.scheduled_at.between(start_date, last_date)
                if start_date and last_date else
                LabServicesQueue.scheduled_at >= start_date if start_date else
                LabServicesQueue.scheduled_at <= last_date
            )

        processed_queue = query.filter(LabServicesQueue.status == QueueStatus.Processed)
        if status is None or status == QueueStatus.Processing:  # by default, get processing
            query = query.filter(LabServicesQueue.status == QueueStatus.Processing)

        elif status == QueueStatus.Processed:
            query = query.filter(LabServicesQueue.status == QueueStatus.Processed)
        else:
            query = query  # apply no filter. filter(LabServicesQueue.status == QueueStatus.Processing)

        count = query.count()
        query = query.order_by(LabServicesQueue.id.desc()).offset(skip).limit(limit)
        results = query.all()

        return {
            'queue': self.generate_queue_list(results),
            'total': count,  # total processing
            'total_processed': processed_queue.count()
        }

    def get_queue(self, queue_id: int) -> LabServicesQueueDTO:
        return self.db_session.query(LabServicesQueue).filter(LabServicesQueue.id == queue_id).first()

    def get_queue_by_booking_id(self, booking_id: int) -> LabServicesQueueDTO:
        return self.db_session.query(LabServicesQueue).filter(LabServicesQueue.booking_id == booking_id).first()

    def get_lab_service_queue_by_booking_id(self, booking_id: int):

        cols = [LabServicesQueue.id.label("queue_id"),
                LabServicesQueue.status,
                LabServicesQueue.booking_id,
                LabServicesQueue.priority,
                ServiceBooking.transaction_id,
                LabServicesQueue.scheduled_at,
                LabService.lab_service_name,
                BusinessServices.ext_turn_around_time
                ]

        result = self.db_session.query(*cols).select_from(LabServicesQueue) \
            .join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .join(LabService, LabService.id == LabServicesQueue.lab_service_id) \
            .join(BusinessServices, BusinessServices.service_id == LabService.service_id) \
            .filter(ServiceBooking.id == booking_id).all()

        response = []

        for res in result:
            sample_elements = self.get_collected_sample_by_queue_id(res.queue_id)
            response.append({
                'queue_id': res.queue_id,
                'status': res.status,
                'booking_id': res.booking_id,
                'priority': res.priority,
                'scheduled_at': res.scheduled_at,
                'lab_service_name': res.lab_service_name,
                'samples': sample_elements,
                'ext_turn_around': res.ext_turn_around_time,
                'transaction_id': res.transaction_id
            })
        return response

    def track_booking_from_queue(self, booking_id: int):
        # get booking elements
        elements = self.get_lab_service_queue_by_booking_id(booking_id)

        service_tracks: List[ServiceTrackingDTO] = []  # List[ServiceTrackingDTO]

        for element in elements:
            complete = 1
            tracks: List[ServiceEventDTO] = []  # List[ServiceEventDTO]

            # add queuing elements
            tracks.append(
                ServiceEventDTO(
                    event_time=str(element["scheduled_at"]),
                    event_desc=(
                        f"{element['lab_service_name']} was scheduled with queue # {element['queue_id']} "
                        f" on a {element['priority']} priority. Current status of this queue item is {element['status']}."
                    ),
                    event_type=EventType.Queuing
                )
            )

            # add sample collection elements
            if len(element["samples"]) > 0:
                complete += 1

            for smpl in element["samples"]:
                tracks.append(
                    ServiceEventDTO(
                        event_time=str(smpl["collected_at"]),
                        event_desc=(
                            f"{smpl['sample_type']} was collected for {element['lab_service_name']}. "
                            f"This is sample # {smpl['id']} for queue #{smpl['queue_id']} and the current status is {smpl['status']}."
                        ),
                        event_type=EventType.SampleCollection
                    )
                )

                # get results
                if smpl["sample_result"] is not None:
                    complete += 1
                    result = smpl["sample_result"]
                    tracks.append(
                        ServiceEventDTO(
                            event_time=str(result["created_at"]),
                            event_desc=(
                                f"Investigation result has been prepared for sample # {result['sample_id']}."
                            ),
                            event_type=EventType.Result,
                        )
                    )

                    # get result verification
                    if result["verification"] is not None:
                        complete += 1
                        verification = (result["verification"]).__dict__
                        tracks.append(
                            ServiceEventDTO(
                                event_time=str(verification["verified_at"]),
                                event_desc=(
                                    f"Result for sample # {result['sample_id']} was verified at {verification['verified_at']}."
                                ),
                                event_type=EventType.Verification,
                            )
                        )

            percentage_complete = (complete / 4) * 100 if complete > 0 else 0

            service_tracks.append(
                ServiceTrackingDTO(
                    queue_id=element["queue_id"],
                    booked_service=element["lab_service_name"],
                    service_tracking_details=tracks,
                    complete=percentage_complete
                )
            )

        # return service_tracks
        transaction_id = elements[0]["transaction_id"] if elements else None
        # return TrackingDataDTO(
        #     service_tracking=service_tracks,
        #     transaction=self.transaction_repository.get_laboratory_transaction(transaction_id),
        # )

        booking_transaction = self.transaction_repository.get_laboratory_transaction(transaction_id)
        booking_transaction['services'] = self.get_lab_services_booking(transaction_id)
        return {
            'service_tracking': service_tracks,
            'transaction': booking_transaction
        }

    def get_result_by_sample_id(self, sample_id: int):

        res = self.db_session.query(SampleResult).filter(SampleResult.sample_id == sample_id).first()

        experiment_repository = ExperimentRepository(self.db_session)

        if res:
            user_repository = UserRepository(self.db_session)
            user = user_repository.get_user_by_id(res.created_by)
            usr = user_repository.get_user(user.username)
            return {
                'id': res.id,
                'sample_id': res.sample_id,
                'comment': res.comment,
                'verification': self.get_result_verification(res.id),
                'created_at': res.created_at,
                'created_by': usr.first_name + " " + usr.last_name,
                'experiment_readings': experiment_repository.get_readings_by_sample_id(res.sample_id)
            }
        return

    def get_result_verification(self, result_id) -> VerifiedResultEntryDTO:
        verification_details = self.db_session.query(LabVerifiedResult) \
            .filter(LabVerifiedResult.result_id == result_id).first()
        if verification_details:
            return VerifiedResultEntryDTO(
                id=verification_details.id,
                result_id=verification_details.result_id,
                verified_at=verification_details.verified_at,
                verified_by=self.user_repository.get_usr_by_id(verification_details.verified_by),
                comment=verification_details.comment,
                status=verification_details.status
            )

        return None

    def get_collected_sample_by_queue_id(self, queue_id: int):
        samples_query = self.db_session.query(CollectedSamples).filter(CollectedSamples.queue_id == queue_id).all()

        collected_samples = []
        for collected_sample in samples_query:
            res = self.get_result_by_sample_id(collected_sample.id)
            collected_samples.append({
                'collected_by': collected_sample.collected_by,
                'collected_at': collected_sample.collected_at,
                'sample_type': collected_sample.sample_type,
                'queue_id': collected_sample.queue_id,
                'status': collected_sample.status,
                'container_label': collected_sample.container_label,
                'id': collected_sample.id,
                'sample_result': res  # self.get_result_by_sample_sample_id(collected_sample.id)
            })
        return collected_samples

    def get_collected_sample_by_sample_id(self, sample_id: int):
        return self.db_session.query(CollectedSamples).filter(CollectedSamples.id == sample_id).first()

    @staticmethod
    def generate_queue_list(results):
        lab_queue_list = []
        for result in results:
            lab_queue_list.append({
                'id': result.id,
                'scheduled_at': result.scheduled_at.isoformat(),
                'lab_service': result.lab_service_name,
                'laboratory': result.laboratory,
                'status': result.status.value,
                'booking_ref': result.booking_id,
                'priority': result.priority.value,
                'est_delivery_time': result.ext_turn_around_time,
                'client_first_name': result.client_first_name,
                'client_last_name': result.client_last_name
            })
        return lab_queue_list

    def update_lab_service_queue(self, lab_service_queue: LabServicesQueue,
                                 new_lab_service_queue_dto: LabServicesQueueDTO) -> LabServicesQueue:
        queue = self.get_queue(lab_service_queue.id)
        queue_data = new_lab_service_queue_dto.dict(exclude_unset=True)
        for var, value in queue_data.items():
            setattr(queue, var, value) if value else None
        self.db_session.commit()
        self.db_session.refresh(lab_service_queue)
        return lab_service_queue

    def delete_lab_service_queue(self, queue_id: int):
        # Get  queuing details
        lab_service_queue = self.get_queue(queue_id)

        # check if queue element doesn't have a collected sample
        if len(self.get_collected_sample_by_queue_id(queue_id)) == 0:

            # Delete booking information

            booking_id = lab_service_queue.booking_id
            self.db_session.query(ServiceBookingDetail).filter(ServiceBookingDetail.id == booking_id).delete()

            self.db_session.delete(lab_service_queue)
            self.db_session.commit()

            return {
                "msg": "Queue deleted successfully",
                "value": True
            }

        else:
            return {
                "msg": "Unable to delete queue. Sample exist",
                "value": False
            }

    def update_lab_queue(self, queue_id, updates: dict) -> LabServicesQueue:
        lab_service_queue: LabServicesQueue = self.get_queue(queue_id)

        if lab_service_queue:
            for key, value in updates.items():
                setattr(lab_service_queue, key, value)
            self.db_session.commit()
            self.db_session.refresh(lab_service_queue)

        return lab_service_queue
