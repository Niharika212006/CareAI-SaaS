"""In-App Notifications and Alerts API Endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.notification import (
    NotificationRead,
    NotificationListResponse,
    UnreadCountResponse,
)
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get authenticated user's notifications",
)
def get_user_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    """Retrieve user notifications ordered newest first."""
    items, total, unread_count = notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return NotificationListResponse(
        items=[NotificationRead.model_validate(item) for item in items],
        total=total,
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count badge",
)
def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UnreadCountResponse:
    """Return total number of unread notifications for badge icon."""
    count = notification_service.get_unread_count(db=db, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark single notification as read",
)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    """Mark a specific notification as read, enforcing user ownership."""
    notification = notification_service.mark_notification_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return NotificationRead.model_validate(notification)


@router.patch(
    "/read-all",
    summary="Mark all user notifications as read",
)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """Bulk mark all unread notifications for the user as read."""
    updated = notification_service.mark_all_notifications_read(
        db=db,
        user_id=current_user.id,
    )
    return {
        "message": "All notifications marked as read.",
        "updated_count": updated,
    }


@router.delete(
    "/{notification_id}",
    summary="Delete a notification",
)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a notification from user history."""
    notification_service.delete_notification(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return {"message": "Notification deleted successfully."}
