import traceback
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from dtos.all import DataResponseDTO
from dtos.lab import CollectedSamplesDTO, SampleDetailDTO, LabServicesQueueDTO, CollectedSamplesCreateDTO
from models.auth import User
from models.client import Person, Client
from models.lab.lab import CollectedSamples, LabService, LabServicesQueue, QueueStatus, SampleType, SampleResult
from models.services.services import ServiceBookingDetail, ServiceBooking, BusinessServices
import datetime

from repos.base_repository import BaseRepository


class CollectedSamplesRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db

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

    def get_sample_result_comments(self):
        return [c.comment for c in self.db.query(SampleResult).all()]

    def add_collected_sample(self, sample_data: CollectedSamplesCreateDTO) -> CollectedSamplesDTO:

        print('smpl-repo:', sample_data)

        smpl = sample_data.__dict__.copy()  # copy to avoid modifying original DTO
        smpl['sample_type'] = self.normalize_sample_type(smpl['sample_type'])

        smpl = sample_data.model_dump(exclude_unset=True, exclude={"id"})
        new_collected_sample = CollectedSamples(**smpl)

        # update queue status as processed
        self.update(sample_data.queue_id, LabServicesQueue, {'status': QueueStatus.Processed})

        self.db.add(new_collected_sample)
        self.db.commit()
        self.db.refresh(new_collected_sample)

        return CollectedSamplesDTO.from_orm(new_collected_sample)

    def get_collected_samples(
            self,
            skip: int = 0,
            limit: int = 10,
            lab_id: int = 0,
            booking_id: int = 0,
            date_filter: dict = None,
            search_keyword: str = None,
            client_id: int = 0
    ) -> DataResponseDTO[CollectedSamplesDTO]:
        """
            Retrieve collected samples from the database with optional filtering, searching, and pagination.

            Args:
                skip (int): Number of records to skip (for pagination).
                limit (int): Maximum number of records to return.
                lab_id (int): Optional lab service ID to filter samples by.
                booking_id (int): Optional booking ID to filter samples by.
                date_filter (dict): Optional date filter with 'start' and 'end' datetime strings or objects.
                    Example: {"start": "2025-10-01", "end": "2025-10-22"}
                search_keyword (str): Keyword to search by patient name, phone, or email.
                client_id (int): Optional filter to restrict samples to a specific client (patient).

            Returns:
                list[CollectedSamples]: List of collected sample ORM objects with related user, person, and queue preloaded.
            """

        # --- Base Query with required joins ---
        query = (
            self.db.query(CollectedSamples)
            .join(CollectedSamples.queue)
            .join(LabServicesQueue.booking)
            .join(ServiceBookingDetail.booking)
            .join(User, CollectedSamples.collected_by == User.id)
            .join(Person, User.person_id == Person.id)
            .options(
                joinedload(CollectedSamples.user).joinedload(User.person),
                joinedload(CollectedSamples.queue),
            )
        )

        # --- Filter: Lab ID ---
        if lab_id:
            query = query.join(LabService, LabService.id == LabServicesQueue.lab_service_id).filter(LabService.lab_id == lab_id)

        # --- Filter: Booking ID ---
        if booking_id:
            query = query.filter(ServiceBookingDetail.booking_id == booking_id)

        # --- Filter: Client ID ---
        if client_id:
            # Join through ServiceBookingDetail → ServiceBooking → Client (via Person)
            query = query.join(Client, Client.person_id == Person.id)
            query = query.filter(Client.id == client_id)

        # --- Filter: Date Range ---
        if date_filter and isinstance(date_filter, dict):

            start = date_filter.get("start_date")
            end = date_filter.get("last_date")
            status = date_filter.get("status")

            if isinstance(start, str):
                start = datetime.datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.datetime.fromisoformat(end)

            if status in ("Processing", "Processed"):
                query = query.filter(CollectedSamples.status == status)

            if start and end:
                query = query.filter(CollectedSamples.collected_at.between(start, end))
            elif start:
                query = query.filter(CollectedSamples.collected_at >= start)
            elif end:
                query = query.filter(CollectedSamples.collected_at <= end)

        # --- Filter: Search Keyword ---
        if search_keyword:
            keyword = f"%{search_keyword}%"
            query = query.filter(
                or_(
                    Person.first_name.ilike(keyword),
                    Person.last_name.ilike(keyword),
                    Person.phone.ilike(keyword),
                    Person.email.ilike(keyword),
                )
            )

        # --- Pagination and ordering ---
        samples = (
            query.order_by(CollectedSamples.collected_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        data = [CollectedSamplesDTO.from_orm(sample) for sample in samples]
        return DataResponseDTO[CollectedSamplesDTO](
            data=data,
            total=query.count()
        )

    def get_sample_by_id(self, sample_id) -> CollectedSamplesDTO | None:
        return CollectedSamplesDTO.from_orm(
            self.db.query(CollectedSamples).filter(CollectedSamples.id == sample_id).first()
        )

    def get_collected_sample_by_queue_id(self, queue_id: int):
        sample = self.db.query(CollectedSamples).filter(CollectedSamples.queue_id == queue_id).first()
        if not sample:
            return None
        return CollectedSamplesDTO.from_orm(
            sample
        )

    def delete_collected_sample(self, sample_id: int) -> None:
        try:
            sample = self.db.query(CollectedSamples).filter(CollectedSamples.id == sample_id).first()

            queue = (
                self.db.query(LabServicesQueue)
                .filter(LabServicesQueue.id == sample.queue_id)
                .first()
            )

            if not queue:
                raise ValueError("Queue not found")

            queue.status = QueueStatus.Processing

            # ✅ ORM delete (tracked)
            self.db.delete(sample)

            self.db.commit()
        except Exception:
            self.db.rollback()
            traceback.print_exc()
            raise

    def update_processed_sample(self, queue_id: int, status: QueueStatus = QueueStatus.Processed) -> bool:
        sample = (
            self.db.query(CollectedSamples)
            .filter(CollectedSamples.queue_id == queue_id)
            .one_or_none()
        )

        if not sample:
            return False

        sample.status = status
        self.db.commit()
        return True
