"""SQLAlchemy database models for AI Assistant conversations and messages."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel
from app.models.user import UserRole


class AIConversation(Base, TimeStampedModel):
    """Stores persistent AI assistant conversation threads scoped to an authenticated user and role."""
    __tablename__ = "ai_conversations"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(
        SQLEnum(UserRole, name="userrole"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False, default="New Conversation")

    # Relationships
    user = relationship("User", backref="conversations")
    messages = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at.asc()",
    )


class AIMessage(Base):
    """Stores individual message turns within an AI assistant conversation."""
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender = Column(String(20), nullable=False)  # "USER" or "ASSISTANT"
    content = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")
