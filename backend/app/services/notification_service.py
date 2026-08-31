"""Centralized In-App Notification and Smart Alert Service."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.user import User


class NotificationService:
    """Encapsulated domain service managing in-app notifications and priority alerts."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create and persist a new notification for a specific recipient user."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            metadata_json=metadata_json or {},
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Notification], int, int]:
        """
        Retrieve paginated notifications strictly scoped to authenticated user_id.
        Returns: (items, total_count, unread_count)
        """
        base_query = db.query(Notification).filter(Notification.user_id == user_id)

        unread_count = (
            db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar() or 0
        )

        if unread_only:
            query = base_query.filter(Notification.is_read == False)
        else:
            query = base_query

        total_count = query.count()
        items = (
            query.order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total_count, unread_count

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Calculate total unread notifications for user badge indicator."""
        return (
            db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar() or 0
        )

    @staticmethod
    def mark_notification_read(
        db: Session,
        user_id: int,
        notification_id: int,
    ) -> Notification:
        """Mark single notification as read, enforcing strict ownership."""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification #{notification_id} not found.",
            )

        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify this notification.",
            )

        if not notification.is_read:
            notification.mark_as_read()
            db.commit()
            db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_notifications_read(db: Session, user_id: int) -> int:
        """Mark all unread notifications for a user as read."""
        now = datetime.now()
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({Notification.is_read: True, Notification.read_at: now}, synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def delete_notification(
        db: Session,
        user_id: int,
        notification_id: int,
    ) -> bool:
        """Delete notification with strict user ownership validation."""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification #{notification_id} not found.",
            )

        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this notification.",
            )

        db.delete(notification)
        db.commit()
        return True


notification_service = NotificationService()
