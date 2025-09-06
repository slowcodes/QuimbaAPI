from typing import Optional, List

from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from sqlalchemy.orm import Session

from dtos.people import ClientNotificationDTO
from models.client import ClientNotification, ClientNotificationSubscription, MsgType


class NotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, notification_id: int) -> Optional[ClientNotification]:
        """
        Retrieve a ClientNotification by its ID.
        """
        try:
            return self.session.query(ClientNotification).filter_by(id=notification_id).one_or_none()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching notification by ID: {e}")

    def get_all(self, limit: int = 100, offset: int = 0) -> List[ClientNotificationDTO]:
        """
        Retrieve all ClientNotification records with pagination.
        """
        cols = [

        ]
        return self.session.query(
            ClientNotification.notification,
            ClientNotification.id,
            ClientNotification.default_sms_msg,
            ClientNotification.default_whatsapp_msg,
            ClientNotification.default_email_msg
        ).select_from(ClientNotification).offset(offset).limit(limit).all()

        # result = []
        # for notification in query:
        #     result.append(
        #         {
        #             'id': notification.id,
        #             'notification': notification.notification,
        #             'default_sms_msg': notification.default_sms_msg,
        #             'default_whatsapp_msg': notification.default_whatsapp_msg,
        #             'default_email_msg': notification.default_sms_msg
        #         }
        #     )
        # return result

    def update(self, notification_id: int, **kwargs) -> ClientNotification:
        """
        Update an existing ClientNotification record.
        """
        notification = self.get_by_id(notification_id)
        if not notification:
            raise NoResultFound(f"ClientNotification with ID {notification_id} not found.")
        try:
            for key, value in kwargs.items():
                if hasattr(notification, key):
                    setattr(notification, key, value)
            self.session.commit()
            return notification
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error updating notification: {e}")

    def delete_notification(self, notification_id: int) -> bool:
        """
        Delete a ClientNotification by its ID.
        """
        notification = self.get_by_id(notification_id)
        if not notification:
            return False
        try:
            self.session.delete(notification)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error deleting notification: {e}")

    def create_subscription(self, client_id: int, msg_type: MsgType) -> ClientNotificationSubscription:
        """
        Create a new subscription for a client.
        """
        new_subscription = ClientNotificationSubscription(client_id=client_id, msg_type=msg_type)
        try:
            self.session.add(new_subscription)
            self.session.commit()
            return new_subscription
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating subscription: {e}")

    def get_subscriptions_by_client(self, client_id: int, limit: int = 100, offset: int = 0) -> List[dict]:
        """
        Get all subscriptions for a specific client with pagination.
        """
        # Retrieve all notification types
        notification_types = self.get_all(limit=limit, offset=offset)

        # Ensure notification_types contains dictionaries or appropriate mappings
        subs = []

        for notification_type in notification_types:
            # Safely extract the notification_id (ensure the structure matches the return type of self.get_all())
            notification_id = notification_type['id'] if isinstance(notification_type, dict) else notification_type.id
            notification_name = notification_type['notification'] if isinstance(notification_type,
                                                                                dict) else notification_type.notification

            # Get all subscriptions for the given client and notification type
            type_subscriptions = (
                self.session.query(ClientNotificationSubscription)
                .filter_by(client_id=client_id, notification_id=notification_id)
                .all()
            )

            # Construct the subscription list
            subscriptions = [
                {
                    'id': t_sub.id,
                    'msg_type': t_sub.msg_type,
                    'created_at': t_sub.created_at.isoformat()  # Serialize datetime
                }
                for t_sub in type_subscriptions
            ]

            # Append the result for the current notification type
            subs.append({
                'notification_id': notification_id,
                'notify': notification_name,
                'subscriptions': subscriptions,
            })

        return subs

    def delete_subscription(self, subscription_id: int) -> bool:
        """
        Delete a subscription by its ID.
        """
        subscription = self.session.query

    def update_client_notification(self, client_id: int, notification_id: int, msg_type: MsgType, state: bool) -> ClientNotificationSubscription:
        """
        Update a specific notification for a client. If the notification is not found, add it with the state set to false.
        """
        print(client_id,notification_id,msg_type,)
        try:
            subscription = self.session.query(ClientNotificationSubscription).filter_by(
                client_id=client_id,
                notification_id=notification_id,
                msg_type=msg_type
            ).one_or_none()

            if not subscription:
                # If the subscription is not found, create a new one with state set to false
                subscription = ClientNotificationSubscription(
                    client_id=client_id,
                    notification_id=notification_id,
                    msg_type=msg_type,
                )
                self.session.add(subscription)
            else:
                # Update the existing subscription's state
                subscription.state = state

            self.session.commit()
            return subscription
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error updating client notification: {e}")