from sqlalchemy.orm import Session
from dtos.lab import CollectedSamplesDTO, SampleDetailDTO, LabServicesQueueDTO
from models.auth import User
from models.client import Person, Client
from models.lab.lab import CollectedSamples, LabService, LabServicesQueue, QueueStatus, SampleType
from models.services import ServiceBookingDetail, ServiceBooking, BusinessServices
from repos.auth_repository import UserRepository
from repos.client.client_repository import ClientRepository
from repos.lab.queue_repository import QueueRepository


class CollectedSamplesRepository:
    def __init__(self, db: Session):
        self.db = db
        self.cols = [
            CollectedSamples.id.label("sample_id"),
            CollectedSamples.sample_type,
            CollectedSamples.collected_at,
            CollectedSamples.container_label,
            CollectedSamples.collected_by,
            CollectedSamples.queue_id,
            CollectedSamples.status,

            LabServicesQueue.id,
            LabServicesQueue.status.label("queue_status"),
            LabServicesQueue.lab_service_id,
            LabServicesQueue.priority,
            LabServicesQueue.scheduled_at.label("queue_booked_at"),

            User.username,

            Person.first_name,
            Person.last_name,

            ServiceBookingDetail.service_id.label("booking_service_id"),
            ServiceBookingDetail.id.label("service_booking_id"),

            ServiceBooking.client_id,

            LabService.lab_service_name,
            LabService.service_id,

            BusinessServices.ext_turn_around_time
        ]
        self.samples_collection_details = self.db.query(*self.cols).select_from(CollectedSamples) \
            .join(LabServicesQueue, LabServicesQueue.id == CollectedSamples.queue_id) \
            .join(User, User.id == CollectedSamples.collected_by) \
            .join(ServiceBookingDetail, ServiceBookingDetail.id == LabServicesQueue.booking_id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .join(Client, Client.id == ServiceBooking.client_id) \
            .join(Person, Person.id == Client.person_id) \
            .join(LabService, LabService.service_id == ServiceBookingDetail.service_id) \
            .join(BusinessServices, LabService.service_id == BusinessServices.service_id)

    def response_model(self, sample) -> SampleDetailDTO:
        user_repo = UserRepository(self.db)
        client_repo = ClientRepository(self.db)
        client = client_repo.get_client(sample.client_id)

        return {
            'sample_type': sample.sample_type,
            'sample_id': sample.sample_id,
            'collected_at': sample.collected_at,
            'container_label': sample.container_label,
            'sample_status': sample.status,
            'lab_service_id': sample.lab_service_id,
            'ext_turn_around': sample.ext_turn_around_time,
            'client': {
                'first_name': sample.first_name,
                'last_name': sample.last_name,
                'sex': client['sex'],
                'date_of_birth': client['date_of_birth']
            },
            'lab_service_name': sample.lab_service_name,
            'queue': {
                'queue_status': sample.queue_status,
                'queue_priority': sample.priority,
                'queue_id': sample.queue_id,
                'queue_booking_time': sample.queue_booked_at
            },
            'user': user_repo.get_user(sample.username)
        }

    def get_collected_sample_by_id(self, sample_id: int):
        return self.response_model(
            self.samples_collection_details.filter(CollectedSamples.id == sample_id).first()
        )

    def normalize_sample_type(self, sample_type):
        """Normalize sample_type to a proper SampleType enum member."""
        if isinstance(sample_type, SampleType):
            return sample_type  # Already correct enum member
        if isinstance(sample_type, str):
            # Try name first
            if sample_type in SampleType.__members__:
                return SampleType[sample_type]
            # Try value
            try:
                return SampleType(sample_type)
            except ValueError:
                raise ValueError(f"Invalid sample_type: {sample_type!r}")
        raise TypeError(f"sample_type must be str or SampleType, got {type(sample_type).__name__}")

    def add_collected_sample(self, sample_data: CollectedSamplesDTO) -> CollectedSamplesDTO:
        smpl = sample_data.__dict__.copy()  # copy to avoid modifying original DTO
        smpl['sample_type'] = self.normalize_sample_type(smpl['sample_type'])

        new_collected_sample = CollectedSamples(**smpl)
        self.db.add(new_collected_sample)
        self.db.commit()
        self.db.refresh(new_collected_sample)

        return CollectedSamplesDTO(
            id=new_collected_sample.id,
            queue_id=new_collected_sample.queue_id,
            container_label=new_collected_sample.container_label,
            collected_at=new_collected_sample.collected_at,
            sample_type=new_collected_sample.sample_type,
            collected_by=new_collected_sample.collected_by
        )

    def get_collected_samples(self, skip: int = 0, limit: int = 10,
                              lab_id: int = 0, booking_id: int = 0, date_filter: dict = None,
                              search_keyword: str = None):
        samples_collection = self.samples_collection_details

        if date_filter:
            start_date = date_filter['start_date']
            last_date = date_filter['last_date']
            status = date_filter['status']

            if start_date:
                samples_collection = samples_collection.filter(CollectedSamples.collected_at >= start_date)
            if last_date:
                samples_collection = samples_collection.filter(CollectedSamples.collected_at <= last_date)
            if status == QueueStatus.Processed or status == QueueStatus.Processing:
                samples_collection = samples_collection.filter(CollectedSamples.status == status)

        if lab_id != 0:
            samples_collection = self.samples_collection_details.where(LabService.lab_id == lab_id)

        if search_keyword:
            samples_collection = samples_collection.filter(
                LabService.lab_service_name.ilike(f"%{search_keyword}%") |
                Person.first_name.ilike(f"%{search_keyword}%") |
                Person.last_name.ilike(f"%{search_keyword}%") |
                # User.username.ilike(f"%{search_keyword}%") |
                CollectedSamples.container_label.ilike(f"%{search_keyword}%")
            )

        samples_collection_details = samples_collection  # .filter(CollectedSamples.status != QueueStatus.Processed)

        if booking_id != 0:
            samples_collection_details = samples_collection.filter(ServiceBooking.id == booking_id)

        total = samples_collection_details.count()
        collected_samples = samples_collection_details.order_by(CollectedSamples.collected_at.desc()) \
            .offset(skip).limit(limit).all()

        data = []
        for sample in collected_samples:
            data.append(
                self.response_model(sample)
            )

        return {
            'data': data,
            'total': total
        }

    def get_sample_by_id(self, sample_id):
        return self.db.query(CollectedSamples).filter(CollectedSamples.id == sample_id).first()

    def delete_collected_sample(self, sample_id: int) -> None:
        sample = self.get_sample_by_id(sample_id)

        queue_repo = QueueRepository(self.db)
        queue = queue_repo.get_queue(sample.queue_id)

        status_dict = LabServicesQueueDTO(
            id=queue.id,
            lab_service_id=queue.lab_service_id,
            booking_id=queue.booking_id,
            status=QueueStatus.Processing
        )
        # status_dict = {
        #     "status": QueueStatus.Processing
        # }
        queue_repo.update_lab_service_queue(queue, status_dict)

        sample = self.get_sample_by_id(sample_id)
        self.db.delete(sample)
        self.db.commit()

    def update_processed_sample(self, sample_id: int, status: QueueStatus = QueueStatus.Processed) -> bool:
        sample = self.get_sample_by_id(sample_id)
        if sample:
            # for key, value in new_data.items():
            #     setattr(sample, key, value)
            # self.session.commit()
            setattr(sample, 'status', status)
            self.db.commit()
            return True

        return False
