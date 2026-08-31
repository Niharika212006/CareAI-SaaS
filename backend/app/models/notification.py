"""Notification model and Type/Priority Enums."""
import enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class NotificationType(str, enum.Enum):
    """Category classification of in-app notifications."""
    APPOINTMENT = "APPOINTMENT"
    PRESCRIPTION = "PRESCRIPTION"
    DOCTOR_APPROVAL = "DOCTOR_APPROVAL"
    AI_SAFETY = "AI_SAFETY"
    SYSTEM = "SYSTEM"


class NotificationPriority(str, enum.Enum):
    """Urgency level of notification."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Notification(Base, TimeStampedModel):
    """In-app notification entity stored in database and dispatched to users."""
    __tablename__ = "notifications"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        Enum(NotificationType),
        default=NotificationType.SYSTEM,
        nullable=False,
        index=True,
    )
    priority = Column(
        Enum(NotificationPriority),
        default=NotificationPriority.NORMAL,
        nullable=False,
        index=True,
    )
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def mark_as_read(self) -> None:
        """Mark notification as read with current timestamp."""
        self.is_read = True
        self.read_at = datetime.now()

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.notification_type}', is_read={self.is_read})>"
