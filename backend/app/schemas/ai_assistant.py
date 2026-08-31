"""Pydantic schemas for the centralized role-aware CareAI Assistant."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class AIChatRequest(BaseModel):
    """Payload for user interaction with the CareAI Assistant."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The message or inquiry sent to the CareAI Assistant.",
    )
    conversation_id: Optional[int] = Field(
        default=None,
        description="Optional existing conversation thread ID to continue context.",
    )


class AIMessageRead(BaseModel):
    """Schema representing an individual stored message turn."""
    id: int
    conversation_id: int
    sender: str
    content: str
    model_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIConversationSummary(BaseModel):
    """Summary overview of a user conversation thread for navigation lists."""
    id: int
    user_id: int
    role: UserRole
    title: str
    message_count: int = 0
    last_message_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIConversationRead(BaseModel):
    """Detailed conversation thread including all ordered message history."""
    id: int
    user_id: int
    role: UserRole
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AIMessageRead] = []

    model_config = ConfigDict(from_attributes=True)


class AIChatResponse(BaseModel):
    """Response returned by the CareAI Assistant after processing an interaction turn."""
    conversation_id: int
    assistant_response: str
    role: str
    model_name: str
    created_at: datetime
    safety_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
