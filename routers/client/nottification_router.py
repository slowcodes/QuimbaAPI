from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from commands.people import ClientNotificationDTO
from db import get_db
from models.client import MsgType
from repos.client.notification_repository import NotificationRepository

notification_router = APIRouter(
    prefix="/api/client/notification",
    tags=["Notifications", "Client"],
)


def get_notification_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)


# Dependency for the repository
def get_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(session=db)


@notification_router.get("/{notification_id}")
def get_notification(
        notification_id: int,
        repository: NotificationRepository = Depends(get_repository)):
    """
    Retrieve a notification by ID.
    """
    notification = repository.get_by_id(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@notification_router.get("/", response_model=List[ClientNotificationDTO])
def get_all_notifications(
        limit: int = 100,
        offset: int = 0,
        repository: NotificationRepository = Depends(get_repository),
):
    """
    Retrieve all notifications with optional pagination.
    """
    return repository.get_all(limit=limit, offset=offset)


@notification_router.put("/{notification_id}")
def update_notification(
        notification_id: int,
        payload: dict,
        repository: NotificationRepository = Depends(get_repository),
):
    """
    Update a notification by ID.
    """
    try:
        updated_notification = repository.update(notification_id, **payload)
        if not updated_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )
        return updated_notification
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@notification_router.post("/subscriptions")
def create_subscription(
        client_id: int,
        msg_type: MsgType,
        repository: NotificationRepository = Depends(get_repository),
):
    """
    Create a new subscription for a client.
    """
    try:
        subscription = repository.create_subscription(client_id=client_id, msg_type=msg_type)
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@notification_router.get("/subscriptions/{client_id}")
def get_subscriptions_by_client(
        client_id: int,
        limit: int = 100,
        offset: int = 0,
        repository: NotificationRepository = Depends(get_repository),
):
    """
    Retrieve all subscriptions for a specific client.
    """
    return repository.get_subscriptions_by_client(client_id=client_id, limit=limit, offset=offset)


@notification_router.delete("/subscriptions/{subscription_id}")
def delete_subscription(
        subscription_id: int,
        repository: NotificationRepository = Depends(get_repository)
):
    """
    Delete a subscription by ID.
    """
    success = repository.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return {"detail": "Subscription deleted successfully"}


@notification_router.put("/subscriptions/")
def update_client_notification(
        client_id: int,
        state: bool,
        notification_id: int,
        notification_type: MsgType,
        repository: NotificationRepository = Depends(get_notification_repository)
):
    """
    Update a specific notification for a client. If the notification is not found, add it with the state set to false.
    """
    try:
        updated_subscription = repository.update_client_notification(client_id, notification_id, notification_type, state)
        return updated_subscription
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
