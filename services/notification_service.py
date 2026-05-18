import asyncio
import json
import logging
from datetime import date
from typing import Any, Dict, Iterable, List, NamedTuple, Optional

from sqlalchemy.orm import Session

from db import SessionLocal
from models.auth import AccountStatus, User
from models.client import Client, Person
from models.consultation import ConsultationQueue
from models.lab.lab import (
    ApprovedLabBookingResult,
    CollectedSamples,
    LabServicesQueue,
    LabVerifiedResult,
    QueueStatus,
    SampleResult,
)
from models.notification import Notification
from models.services.services import BookingStatus, ServiceBooking, ServiceBookingDetail
from models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)


NOTIFICATION_GENERATION_INTERVAL_SECONDS = 60 * 60


class GeneratedNotification(NamedTuple):
    title: str
    description: str
    message: str


class UserNotificationService:
    def __init__(self, db: Session):
        self.db = db

    def generate_notifications(self) -> int:
        notifications = list(self._build_notifications())
        if not notifications:
            return 0

        users = (
            self.db.query(User.id)
            .filter(User.status != AccountStatus.Deleted)
            .all()
        )

        created = 0
        for user in users:
            for notification in notifications:
                if self._is_same_as_latest(user.id, notification):
                    continue
                self.db.add(
                    Notification(
                        title=notification.title,
                        description=notification.description,
                        message=notification.message,
                        user_id=user.id,
                    )
                )
                created += 1

        if created:
            self.db.commit()

        return created

    def _build_notifications(self) -> Iterable[GeneratedNotification]:
        processing_lab_queue = self._processing_lab_queue_items()
        if processing_lab_queue:
            yield GeneratedNotification(
                title="Lab queue processing",
                description=f"{len(processing_lab_queue)} lab service queue item(s) are still processing.",
                message=self._serialize_message(processing_lab_queue),
            )

        processing_samples = self._processing_collected_sample_items()
        if processing_samples:
            yield GeneratedNotification(
                title="Collected samples processing",
                description=f"{len(processing_samples)} collected sample(s) are still processing.",
                message=self._serialize_message(processing_samples),
            )

        unverified_results = self._unverified_result_items()
        if unverified_results:
            yield GeneratedNotification(
                title="Unverified lab results",
                description=f"{len(unverified_results)} lab result(s) are waiting for verification.",
                message=self._serialize_message(unverified_results),
            )

        unapproved_booking_results = self._unapproved_booking_result_items()
        if unapproved_booking_results:
            yield GeneratedNotification(
                title="Unapproved booking results",
                description=f"{len(unapproved_booking_results)} verified booking result(s) are waiting for approval.",
                message=self._serialize_message(unapproved_booking_results),
            )

        todays_appointments = self._todays_consultation_appointment_items()
        if todays_appointments:
            yield GeneratedNotification(
                title="Today's consultation appointments",
                description=f"{len(todays_appointments)} consultation appointment(s) are scheduled for today.",
                message=self._serialize_message(todays_appointments),
            )

        incomplete_transactions = self._incomplete_payment_transaction_items()
        if incomplete_transactions:
            yield GeneratedNotification(
                title="Incomplete payments",
                description=f"{len(incomplete_transactions)} transaction(s) have incomplete payment.",
                message=self._serialize_message(incomplete_transactions),
            )

    def _is_same_as_latest(self, user_id: int, notification: GeneratedNotification) -> bool:
        latest = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.title == notification.title,
            )
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .first()
        )
        return (
            latest is not None
            and latest.description == notification.description
            and latest.message == notification.message
        )

    @staticmethod
    def _serialize_message(items: List[Dict[str, Any]]) -> str:
        return json.dumps(items, sort_keys=True)

    @staticmethod
    def _format_message_item(
            first_name: Optional[str],
            last_name: Optional[str],
            transaction_id: Optional[int],
            transaction_date: Any,
            queue_id: Optional[int] = None,
            sample_id: Optional[int] = None,
            result_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        item = {
            "client_name": " ".join(filter(None, [first_name, last_name])) or None,
            "transaction_id": transaction_id,
            "transaction_date": transaction_date.isoformat() if transaction_date else None,
        }

        if queue_id is not None:
            item["queue_id"] = queue_id
        if sample_id is not None:
            item["sample_id"] = sample_id
        if result_id is not None:
            item["result_id"] = result_id

        return item

    def _processing_lab_queue_items(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Person.first_name,
                Person.last_name,
                Transaction.id.label("transaction_id"),
                Transaction.transaction_date,
                LabServicesQueue.id.label("queue_id"),
                CollectedSamples.id.label("sample_id"),
                SampleResult.id.label("result_id"),
            )
            .select_from(LabServicesQueue)
            .join(ServiceBookingDetail, LabServicesQueue.booking_id == ServiceBookingDetail.id)
            .join(ServiceBooking, ServiceBookingDetail.booking_id == ServiceBooking.id)
            .join(Client, ServiceBooking.client_id == Client.id)
            .join(Person, Client.person_id == Person.id)
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)
            .outerjoin(CollectedSamples, CollectedSamples.queue_id == LabServicesQueue.id)
            .outerjoin(SampleResult, SampleResult.queue_id == LabServicesQueue.id)
            .filter(LabServicesQueue.status == QueueStatus.Processing)
            .all()
        )
        return [self._format_message_item(*row) for row in rows]

    def _processing_collected_sample_items(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Person.first_name,
                Person.last_name,
                Transaction.id.label("transaction_id"),
                Transaction.transaction_date,
                LabServicesQueue.id.label("queue_id"),
                CollectedSamples.id.label("sample_id"),
                SampleResult.id.label("result_id"),
            )
            .select_from(CollectedSamples)
            .join(LabServicesQueue, CollectedSamples.queue_id == LabServicesQueue.id)
            .join(ServiceBookingDetail, LabServicesQueue.booking_id == ServiceBookingDetail.id)
            .join(ServiceBooking, ServiceBookingDetail.booking_id == ServiceBooking.id)
            .join(Client, ServiceBooking.client_id == Client.id)
            .join(Person, Client.person_id == Person.id)
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)
            .outerjoin(SampleResult, SampleResult.queue_id == LabServicesQueue.id)
            .filter(CollectedSamples.status == QueueStatus.Processing)
            .all()
        )
        return [self._format_message_item(*row) for row in rows]

    def _unverified_result_items(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Person.first_name,
                Person.last_name,
                Transaction.id.label("transaction_id"),
                Transaction.transaction_date,
                LabServicesQueue.id.label("queue_id"),
                CollectedSamples.id.label("sample_id"),
                SampleResult.id.label("result_id"),
            )
            .select_from(SampleResult)
            .outerjoin(LabVerifiedResult, LabVerifiedResult.result_id == SampleResult.id)
            .join(LabServicesQueue, SampleResult.queue_id == LabServicesQueue.id)
            .join(ServiceBookingDetail, LabServicesQueue.booking_id == ServiceBookingDetail.id)
            .join(ServiceBooking, ServiceBookingDetail.booking_id == ServiceBooking.id)
            .join(Client, ServiceBooking.client_id == Client.id)
            .join(Person, Client.person_id == Person.id)
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)
            .outerjoin(CollectedSamples, CollectedSamples.queue_id == LabServicesQueue.id)
            .filter(LabVerifiedResult.id.is_(None))
            .all()
        )
        return [self._format_message_item(*row) for row in rows]

    def _unapproved_booking_result_items(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Person.first_name,
                Person.last_name,
                Transaction.id.label("transaction_id"),
                Transaction.transaction_date,
                LabServicesQueue.id.label("queue_id"),
                CollectedSamples.id.label("sample_id"),
                SampleResult.id.label("result_id"),
            )
            .select_from(ServiceBooking)
            .outerjoin(ApprovedLabBookingResult, ApprovedLabBookingResult.booking_id == ServiceBooking.id)
            .join(Client, ServiceBooking.client_id == Client.id)
            .join(Person, Client.person_id == Person.id)
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)
            .outerjoin(ServiceBookingDetail, ServiceBookingDetail.booking_id == ServiceBooking.id)
            .outerjoin(LabServicesQueue, LabServicesQueue.booking_id == ServiceBookingDetail.id)
            .outerjoin(CollectedSamples, CollectedSamples.queue_id == LabServicesQueue.id)
            .outerjoin(SampleResult, SampleResult.queue_id == LabServicesQueue.id)
            .filter(
                ServiceBooking.booking_status == BookingStatus.Verified,
                ApprovedLabBookingResult.id.is_(None),
            )
            .all()
        )
        return [self._format_message_item(*row) for row in rows]

    def _todays_consultation_appointment_items(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Person.first_name,
                Person.last_name,
                Transaction.id.label("transaction_id"),
                Transaction.transaction_date,
                ConsultationQueue.id.label("queue_id"),
            )
            .select_from(ConsultationQueue)
            .join(ServiceBookingDetail, ConsultationQueue.booking_id == ServiceBookingDetail.id)
            .join(ServiceBooking, ServiceBookingDetail.booking_id == ServiceBooking.id)
            .join(Client, ServiceBooking.client_id == Client.id)
            .join(Person, Client.person_id == Person.id)
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)
            .filter(
                ConsultationQueue.scheduled_at == date.today(),
                ConsultationQueue.status == QueueStatus.Processing,
            )
            .all()
        )
        return [
            self._format_message_item(
                row.first_name,
                row.last_name,
                row.transaction_id,
                row.transaction_date,
                queue_id=row.queue_id,
            )
            for row in rows
        ]

    def _incomplete_payment_transaction_items(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Person.first_name,
                Person.last_name,
                Transaction.id.label("transaction_id"),
                Transaction.transaction_date,
            )
            .select_from(Transaction)
            .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id)
            .join(Client, ServiceBooking.client_id == Client.id)
            .join(Person, Client.person_id == Person.id)
            .filter(Transaction.transaction_status == TransactionType.Open)
            .all()
        )
        return [
            self._format_message_item(
                row.first_name,
                row.last_name,
                row.transaction_id,
                row.transaction_date,
            )
            for row in rows
        ]


def generate_user_notifications() -> int:
    db = SessionLocal()
    try:
        return UserNotificationService(db).generate_notifications()
    except Exception:
        db.rollback()
        logger.exception("Failed to generate user notifications")
        return 0
    finally:
        db.close()


async def run_hourly_user_notification_generator() -> None:
    while True:
        generate_user_notifications()
        await asyncio.sleep(NOTIFICATION_GENERATION_INTERVAL_SECONDS)
