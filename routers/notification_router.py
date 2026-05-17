from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dtos.all import NotificationDTO
from dtos.auth import UserDTO
from repos.notification_repository import UserNotificationRepository
from security.dependencies import get_current_active_user

user_notification_router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["User Notifications"],
)


def get_user_notification_repository(db: Session = Depends(get_db)) -> UserNotificationRepository:
    return UserNotificationRepository(db)


@user_notification_router.get("/", response_model=List[NotificationDTO])
def get_user_notifications(
        limit: int = 100,
        offset: int = 0,
        unread_only: bool = False,
        repository: UserNotificationRepository = Depends(get_user_notification_repository), *,
        current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repository.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )


@user_notification_router.get("/{notification_id}", response_model=NotificationDTO)
def get_user_notification(
        notification_id: int,
        repository: UserNotificationRepository = Depends(get_user_notification_repository), *,
        current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    notification = repository.get_user_notification(current_user.id, notification_id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return notification


@user_notification_router.put("/{notification_id}/status", response_model=NotificationDTO)
def update_user_notification_status(
        notification_id: int,
        is_read: bool,
        repository: UserNotificationRepository = Depends(get_user_notification_repository), *,
        current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    notification = repository.update_status(current_user.id, notification_id, is_read)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return notification
