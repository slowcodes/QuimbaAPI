import asyncio
import logging
from datetime import date
from typing import Iterable, NamedTuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from db import SessionLocal
from models.auth import AccountStatus, User
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
from models.services.services import BookingStatus, ServiceBooking
from models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)


NOTIFICATION_GENERATION_INTERVAL_SECONDS = 60 * 60


class GeneratedNotification(NamedTuple):
    title: str
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
                        message=notification.message,
                        user_id=user.id,
                    )
                )
                created += 1

        if created:
            self.db.commit()

        return created

    def _build_notifications(self) -> Iterable[GeneratedNotification]:
        processing_lab_queue = self._processing_lab_queue_count()
        if processing_lab_queue:
            yield GeneratedNotification(
                title="Lab queue processing",
                message=f"{processing_lab_queue} lab service queue item(s) are still processing.",
            )

        processing_samples = self._processing_collected_samples_count()
        if processing_samples:
            yield GeneratedNotification(
                title="Collected samples processing",
                message=f"{processing_samples} collected sample(s) are still processing.",
            )

        unverified_results = self._unverified_results_count()
        if unverified_results:
            yield GeneratedNotification(
                title="Unverified lab results",
                message=f"{unverified_results} lab result(s) are waiting for verification.",
            )

        unapproved_booking_results = self._unapproved_booking_results_count()
        if unapproved_booking_results:
            yield GeneratedNotification(
                title="Unapproved booking results",
                message=f"{unapproved_booking_results} verified booking result(s) are waiting for approval.",
            )

        todays_appointments = self._todays_consultation_appointments_count()
        if todays_appointments:
            yield GeneratedNotification(
                title="Today's consultation appointments",
                message=f"{todays_appointments} consultation appointment(s) are scheduled for today.",
            )

        incomplete_transactions = self._incomplete_payment_transactions_count()
        if incomplete_transactions:
            yield GeneratedNotification(
                title="Incomplete payments",
                message=f"{incomplete_transactions} transaction(s) have incomplete payment.",
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
        return latest is not None and latest.message == notification.message

    def _processing_lab_queue_count(self) -> int:
        return (
            self.db.query(func.count(LabServicesQueue.id))
            .filter(LabServicesQueue.status == QueueStatus.Processing)
            .scalar()
            or 0
        )

    def _processing_collected_samples_count(self) -> int:
        return (
            self.db.query(func.count(CollectedSamples.id))
            .filter(CollectedSamples.status == QueueStatus.Processing)
            .scalar()
            or 0
        )

    def _unverified_results_count(self) -> int:
        return (
            self.db.query(func.count(SampleResult.id))
            .outerjoin(LabVerifiedResult, LabVerifiedResult.result_id == SampleResult.id)
            .filter(LabVerifiedResult.id.is_(None))
            .scalar()
            or 0
        )

    def _unapproved_booking_results_count(self) -> int:
        return (
            self.db.query(func.count(ServiceBooking.id))
            .outerjoin(ApprovedLabBookingResult, ApprovedLabBookingResult.booking_id == ServiceBooking.id)
            .filter(
                ServiceBooking.booking_status == BookingStatus.Verified,
                ApprovedLabBookingResult.id.is_(None),
            )
            .scalar()
            or 0
        )

    def _todays_consultation_appointments_count(self) -> int:
        return (
            self.db.query(func.count(ConsultationQueue.id))
            .filter(
                ConsultationQueue.scheduled_at == date.today(),
                ConsultationQueue.status == QueueStatus.Processing,
            )
            .scalar()
            or 0
        )

    def _incomplete_payment_transactions_count(self) -> int:
        return (
            self.db.query(func.count(Transaction.id))
            .filter(Transaction.transaction_status == TransactionType.Open)
            .scalar()
            or 0
        )


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
