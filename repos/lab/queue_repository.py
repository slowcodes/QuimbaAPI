from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from dtos.lab import DynamicParameterBaseDTO, DynamicParameterCreateDTO, DynamicParameterDTO, \
    DynamicParameterUpdateDTO, LabServicesQueueDTO, VerifiedResultEntryDTO, SampleResultDTO, LabServicesQueueCreateDTO
from dtos.services import ServiceEventDTO, EventType, ServiceTrackingDTO
from models.client import Client, Person
from models.lab.lab import LabServicesQueue, Laboratory, QueueStatus, LabService, CollectedSamples, SampleResult, \
    LabVerifiedResult, DynamicParameter
from models.services.services import ServiceBooking, BusinessServices, ServiceBookingDetail
from repos.auth_repository import UserRepository
from repos.lab.lab_repository import LabRepository
from repos.lab.sample_repository import CollectedSamplesRepository
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
        self.lab_repository = LabRepository(self.db_session)
        self.service_repository = ServiceRepository(self.db_session)
        self.sample_repository = CollectedSamplesRepository(self.db_session)

    def create_lab_service_queue(self, lab_service_queue_dto: LabServicesQueueCreateDTO) -> LabServicesQueueDTO:
        lab_service_queue = LabServicesQueue(**lab_service_queue_dto.dict())
        self.db_session.add(lab_service_queue)
        self.db_session.commit()
        self.db_session.refresh(lab_service_queue)

        return LabServicesQueueDTO.from_orm(lab_service_queue)

    def search_lab_service_queue(self, keyword='', skip=0, limit=10, lab_id: int = 0) :
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

    def get_lab_service_queue(
        self,
        lab_id: int = 0,
        skip: int = 0,
        limit: int = 10,
        booking_id: int = 0,
        last_date: str = None,
        start_date: str = None,
        status: str = QueueStatus.Processing,
        client_id: int = 0,
        search_text: str = "",
        lab_service_id: int = 0,
    ):

        base_query = self.db_session.query(LabServicesQueue)
        needs_lab_service = lab_id != 0 or lab_service_id != 0 or bool(search_text)
        needs_booking = client_id != 0 or booking_id != 0 or bool(search_text)

        if needs_lab_service:
            base_query = base_query.join(LabService, LabServicesQueue.lab_service_id == LabService.id)
            if lab_id != 0:
                base_query = base_query.join(Laboratory, Laboratory.id == LabService.lab_id).filter(Laboratory.id == lab_id)
            if lab_service_id != 0:
                base_query = base_query.filter(LabService.id == lab_service_id)

        if needs_booking:
            base_query = base_query.join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id)
            if client_id != 0 or search_text:
                base_query = base_query.join(ServiceBooking, ServiceBookingDetail.booking_id == ServiceBooking.id) \
                    .join(Client, Client.id == ServiceBooking.client_id)
            if search_text:
                base_query = base_query.join(Person, Person.id == Client.person_id)
            if client_id != 0:
                base_query = base_query.filter(Client.id == client_id)

        if booking_id != 0:
            base_query = base_query.filter(ServiceBookingDetail.booking_id == booking_id)

        if search_text:
            search_value = f"%{search_text}%"
            base_query = base_query.filter(
                (Person.first_name.ilike(search_value)) |
                (Person.last_name.ilike(search_value)) |
                (func.concat(Person.first_name, " ", Person.last_name).ilike(search_value)) |
                (Person.phone.ilike(search_value)) |
                (LabService.lab_service_name.ilike(search_value))
            )

        if last_date is not None and start_date is not None:
            last_date = last_date + " 23:59:59.000001"
            start_date = start_date + " 00:00:00.000001"
            base_query = base_query.filter(
                LabServicesQueue.scheduled_at.between(start_date, last_date)
                if start_date and last_date else
                LabServicesQueue.scheduled_at >= start_date if start_date else
                LabServicesQueue.scheduled_at <= last_date
            )

        processed_queue = base_query.filter(LabServicesQueue.status == QueueStatus.Processed)

        if status in QueueStatus.__members__:
            base_query = base_query.filter(LabServicesQueue.status == status)

        count = base_query.count()
        query = base_query.order_by(LabServicesQueue.id.desc()).offset(skip).limit(limit)
        results = query.all()

        return {
            'queue': [LabServicesQueueDTO.from_orm(queue) for queue in results],
            'total': count,  # total processing
            'total_processed': processed_queue.count()
        }

    def get_queue(self, queue_id: int) -> LabServicesQueueDTO:
        return LabServicesQueueDTO.from_orm(
            self.db_session.query(LabServicesQueue).filter(LabServicesQueue.id == queue_id).first()
        )

    def get_queue_by_booking_id(self, booking_id: int) -> LabServicesQueueDTO:
        return self.db_session.query(LabServicesQueue).filter(LabServicesQueue.booking_id == booking_id).first()

    def get_dynamic_parameters(self, queue_id: int) -> list[DynamicParameterDTO]:
        return [
            DynamicParameterDTO.from_orm(dynamic_parameter)
            for dynamic_parameter in self.db_session.query(DynamicParameter)
            .filter(DynamicParameter.lab_service_queue_id == queue_id)
            .order_by(DynamicParameter.id.asc())
            .all()
        ]

    def create_dynamic_parameter(self, dynamic_parameter: DynamicParameterCreateDTO) -> DynamicParameterDTO:
        queue = self.db_session.query(LabServicesQueue).filter(
            LabServicesQueue.id == dynamic_parameter.lab_service_queue_id
        ).first()
        if queue is None:
            return None

        db_dynamic_parameter = DynamicParameter(**dynamic_parameter.dict())
        self.db_session.add(db_dynamic_parameter)
        self.db_session.commit()
        self.db_session.refresh(db_dynamic_parameter)
        return DynamicParameterDTO.from_orm(db_dynamic_parameter)

    def update_dynamic_parameter(
        self,
        dynamic_parameter_id: int,
        dynamic_parameter: DynamicParameterUpdateDTO,
    ) -> DynamicParameterDTO | None:
        db_dynamic_parameter = self.db_session.query(DynamicParameter).filter(
            DynamicParameter.id == dynamic_parameter_id
        ).first()
        if db_dynamic_parameter is None:
            return None

        for key, value in dynamic_parameter.dict(exclude_unset=True).items():
            setattr(db_dynamic_parameter, key, value)
        self.db_session.commit()
        self.db_session.refresh(db_dynamic_parameter)
        return DynamicParameterDTO.from_orm(db_dynamic_parameter)

    def replace_dynamic_parameters(
        self,
        queue_id: int,
        dynamic_parameters: list[DynamicParameterBaseDTO],
    ) -> list[DynamicParameterDTO] | None:
        queue = self.db_session.query(LabServicesQueue).filter(LabServicesQueue.id == queue_id).first()
        if queue is None:
            return None

        self.db_session.query(DynamicParameter).filter(
            DynamicParameter.lab_service_queue_id == queue_id
        ).delete(synchronize_session=False)

        saved_parameters = []
        for dynamic_parameter in dynamic_parameters:
            db_dynamic_parameter = DynamicParameter(
                lab_service_queue_id=queue_id,
                parameter=dynamic_parameter.parameter,
                parameter_value=dynamic_parameter.parameter_value,
                exp_id=dynamic_parameter.exp_id,
            )
            self.db_session.add(db_dynamic_parameter)
            saved_parameters.append(db_dynamic_parameter)

        self.db_session.commit()
        for dynamic_parameter in saved_parameters:
            self.db_session.refresh(dynamic_parameter)
        return [DynamicParameterDTO.from_orm(dynamic_parameter) for dynamic_parameter in saved_parameters]

    def delete_dynamic_parameter(self, dynamic_parameter_id: int) -> bool:
        db_dynamic_parameter = self.db_session.query(DynamicParameter).filter(
            DynamicParameter.id == dynamic_parameter_id
        ).first()
        if db_dynamic_parameter is None:
            return False

        self.db_session.delete(db_dynamic_parameter)
        self.db_session.commit()
        return True

    def get_lab_service_queue_by_booking_id(self, booking_id: int):
        q_result = self.db_session.query(LabServicesQueue) \
            .join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
            .filter(ServiceBookingDetail.booking_id == booking_id).all()

        return [LabServicesQueueDTO.from_orm(queue) for queue in q_result]


    def get_result_by_sample_id(self, sample_id: int):
        res = self.db_session.query(SampleResult).filter(SampleResult.sample_id == sample_id).first()
        if res:
            return [SampleResultDTO.from_orm(res)]
        return None

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
        # self.db_session.refresh(lab_service_queue)
        return lab_service_queue

    def delete_lab_service_queue(self, queue_id: int):
        # Get  queuing details
        lab_service_queue = self.db_session.query(LabServicesQueue).filter(LabServicesQueue.id == queue_id).first()

        # check if queue element doesn't have a collected sample
        if self.sample_repository.get_collected_sample_by_queue_id(queue_id) is None:

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
        lab_service_queue = self.db_session.query(LabServicesQueue).filter(LabServicesQueue.id == queue_id).first()

        if lab_service_queue:
            for key, value in updates.items():
                setattr(lab_service_queue, key, value)
            self.db_session.commit()
            self.db_session.refresh(lab_service_queue)

        return lab_service_queue
