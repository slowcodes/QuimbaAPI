import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from dtos.all import NotificationDTO
from models.notification import Notification


class UserNotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_user_notifications(
            self,
            user_id: int,
            limit: int = 100,
            offset: int = 0,
            unread_only: bool = False,
    ) -> List[NotificationDTO]:
        query = (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )

        if unread_only:
            query = query.filter(Notification.is_read.is_(False))

        return [
            self._to_dto(notification)
            for notification in query.offset(offset).limit(limit).all()
        ]

    def get_user_notification(self, user_id: int, notification_id: int) -> Optional[NotificationDTO]:
        notification = self._get_user_notification_model(user_id, notification_id)
        if notification is None:
            return None
        return self._to_dto(notification)

    def update_status(self, user_id: int, notification_id: int, is_read: bool) -> Optional[NotificationDTO]:
        notification = self._get_user_notification_model(user_id, notification_id)
        if notification is None:
            return None

        notification.is_read = is_read
        self.session.commit()
        self.session.refresh(notification)
        return self._to_dto(notification)

    def _get_user_notification_model(self, user_id: int, notification_id: int) -> Optional[Notification]:
        return (
            self.session.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .one_or_none()
        )

    @staticmethod
    def _to_dto(notification: Notification) -> NotificationDTO:
        return NotificationDTO(
            id=notification.id,
            title=notification.title,
            description=notification.description,
            message=UserNotificationRepository._parse_message(notification.message),
            user_id=notification.user_id,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat() if notification.created_at else "",
        )

    @staticmethod
    def _parse_message(message: Optional[str]) -> List[Dict[str, Any]]:
        if not message:
            return []

        try:
            parsed = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return [{"message": message}]

        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            return [parsed]
        return []
