"""Pydantic schemas for In-App Notifications and Alerts."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType, NotificationPriority


class NotificationBase(BaseModel):
    """Shared base properties for a notification."""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata_json: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Payload for creating a notification."""
    user_id: int


class NotificationRead(NotificationBase):
    """Public read model for user notifications."""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    """Unread badge counter response."""
    unread_count: int


class NotificationListResponse(BaseModel):
    """Paginated list response of user notifications."""
    items: List[NotificationRead]
    total: int
    unread_count: int

    model_config = ConfigDict(from_attributes=True)
