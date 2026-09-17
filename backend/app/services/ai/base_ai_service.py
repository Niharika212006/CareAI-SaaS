"""Base AI Service orchestrating conversation state, live database context, and response generation."""
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.ai_assistant import AIConversation, AIMessage
from app.schemas.ai_assistant import AIChatRequest, AIChatResponse
from app.services.ai.safety_service import safety_service
from app.services.ai.gemini_provider import gemini_provider
from app.services.ai.response_validation import response_validator

logger = logging.getLogger("healthcare.ai.base")

MAX_CONTEXT_MESSAGES = 10
MAX_CONTEXT_CHARACTERS = 8000


class BaseAIService:
    """Foundational service for role-aware AI interactions."""

    def __init__(self, role: UserRole) -> None:
        self.role = role

    def _generate_title(self, message: str) -> str:
        """Create a clean, concise title from initial user prompt."""
        cleaned = message.strip().replace("\n", " ")
        if len(cleaned) <= 45:
            return cleaned
        return cleaned[:42].rsplit(" ", 1)[0] + "..."

    def _retrieve_live_context(self, db: Session, user: User, query: str) -> Dict[str, Any]:
        """Override in subclasses to provide real, role-authorized database context."""
        return {}

    def _get_system_prompt(self) -> str:
        """Override in subclasses to return role-specific instructions."""
        raise NotImplementedError

    def _assemble_prompt(
        self,
        previous_messages: List[AIMessage],
        current_message: str,
        user: User,
        live_context: Dict[str, Any],
    ) -> str:
        """Assemble previous conversation turns + authorized live database ground truth + user message."""
        formatted_history = []
        char_count = len(current_message)

        # Truncate older history turns if exceeding character budget
        reversed_history = list(reversed(previous_messages))
        included = []
        for msg in reversed_history:
            entry_len = len(msg.content) + 20
            if char_count + entry_len > MAX_CONTEXT_CHARACTERS:
                break
            char_count += entry_len
            included.append(msg)

        for msg in reversed(included):
            sender = "User" if msg.sender == "USER" else "CareAI Assistant"
            formatted_history.append(f"[{sender}]: {msg.content}")

        history_block = (
            "\n".join(formatted_history)
            if formatted_history
            else "(No prior conversation messages in this thread.)"
        )

        context_str = json.dumps(live_context, indent=2, default=str) if live_context else "(No database context needed)"

        user_prompt = (
            f"=== ACTIVE USER INFO ===\n"
            f"Name: {user.full_name}\n"
            f"Role: {user.role.value}\n\n"
            f"=== AUTHORIZED LIVE DATABASE CONTEXT (VERIFIED APPLICATION DATA) ===\n"
            f"{context_str}\n\n"
            f"=== CONVERSATION HISTORY ===\n"
            f"{history_block}\n\n"
            f"=== CURRENT USER INQUIRY ===\n"
            f"[User]: {current_message}\n\n"
            f"[CareAI Assistant]:"
        )
        return user_prompt

    def process_chat(
        self,
        db: Session,
        user: User,
        request: AIChatRequest,
    ) -> AIChatResponse:
        """Execute a conversational interaction turn with live data grounding."""
        # 1. Resolve or initialize conversation
        conversation: Optional[AIConversation] = None
        if request.conversation_id:
            conversation = (
                db.query(AIConversation)
                .filter(
                    AIConversation.id == request.conversation_id,
                    AIConversation.user_id == user.id,
                )
                .first()
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation thread not found or access denied.",
                )
        else:
            conversation = AIConversation(
                user_id=user.id,
                role=user.role,
                title=self._generate_title(request.message),
            )
            db.add(conversation)
            db.flush()

        # 2. Retrieve history turns
        prior_messages = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at.desc())
            .limit(MAX_CONTEXT_MESSAGES)
            .all()
        )
        prior_messages.sort(key=lambda m: m.created_at)

        # 3. Retrieve verified, role-specific live database context
        live_context = self._retrieve_live_context(db, user, request.message)

        # 4. Assemble bounded prompt
        system_prompt = self._get_system_prompt()
        assembled_prompt = self._assemble_prompt(
            previous_messages=prior_messages,
            current_message=request.message,
            user=user,
            live_context=live_context,
        )

        # 5. Check emergency symptoms
        safety_eval = safety_service.evaluate_emergency_symptoms(request.message)
        is_emergency = safety_eval.get("emergency_symptom_detected", False)

        # 6. Generate response from AI Provider / Clinical Engine
        raw_response = gemini_provider.generate(
            system_prompt=system_prompt,
            user_prompt=assembled_prompt,
            response_mime_type="text/plain",
        )

        # 7. Validate and sanitize response
        validated_response = response_validator.validate_and_format(
            raw_response=raw_response,
            role=self.role,
            emergency_detected=is_emergency,
        )

        # 8. Persist messages in database
        now = datetime.now(timezone.utc)
        user_msg = AIMessage(
            conversation_id=conversation.id,
            sender="USER",
            content=request.message.strip(),
            model_name=None,
            created_at=now,
        )
        assistant_msg = AIMessage(
            conversation_id=conversation.id,
            sender="ASSISTANT",
            content=validated_response.strip(),
            model_name=gemini_provider.model_name,
            created_at=now,
        )
        conversation.updated_at = now
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()

        return AIChatResponse(
            conversation_id=conversation.id,
            assistant_response=validated_response.strip(),
            role=user.role.value,
            model_name=gemini_provider.model_name,
            created_at=now,
            safety_metadata=safety_eval,
        )
