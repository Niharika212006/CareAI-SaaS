"""Business logic service for Centralized Role-Aware CareAI Assistant."""
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.ai.client import ai_client, AIProviderUnavailableError, AIInvalidResponseError
from app.ai.assistant_prompts import get_system_prompt_for_role
from app.models.user import User, UserRole
from app.models.ai_assistant import AIConversation, AIMessage
from app.schemas.ai_assistant import (
    AIChatRequest,
    AIChatResponse,
    AIConversationRead,
    AIConversationSummary,
    AIMessageRead,
)

logger = logging.getLogger("healthcare.ai.assistant")

# Maximum history turns to include as context (5 user + 5 assistant turns)
MAX_CONTEXT_MESSAGES = 10
# Maximum character count for previous conversation context
MAX_CONTEXT_CHARACTERS = 8000

# Emergency symptom keywords for proactive safety metadata flagging
EMERGENCY_KEYWORDS = [
    r"\bchest pain\b",
    r"\bheart attack\b",
    r"\bshortness of breath\b",
    r"\bcan't breathe\b",
    r"\bcannot breathe\b",
    r"\bdifficulty breathing\b",
    r"\bslurred speech\b",
    r"\bfacial drooping\b",
    r"\bstroke\b",
    r"\bunconscious\b",
    r"\bsevere bleeding\b",
    r"\banaphylaxis\b",
    r"\boverdose\b",
    r"\bsuicid",
    r"\bpoison",
]


class AIAssistantService:
    """Service layer managing role-aware AI interactions, context assembly, and conversation persistence."""

    def _generate_title(self, first_message: str) -> str:
        """Create a clean, concise title from the initial user prompt."""
        cleaned = first_message.strip().replace("\n", " ")
        if len(cleaned) <= 45:
            return cleaned
        return cleaned[:42].rsplit(" ", 1)[0] + "..."

    def _evaluate_safety_metadata(self, message: str) -> Optional[dict]:
        """Check for acute emergency signs in user message to tag safety metadata."""
        lower_msg = message.lower()
        for pattern in EMERGENCY_KEYWORDS:
            if re.search(pattern, lower_msg):
                return {
                    "emergency_symptom_detected": True,
                    "triage_guidance": "Emergency warning: Please seek immediate medical care or call local emergency services.",
                }
        return {"emergency_symptom_detected": False}

    def _assemble_bounded_prompt(
        self,
        previous_messages: List[AIMessage],
        current_message: str,
        user_role: UserRole,
        user_name: str,
    ) -> str:
        """
        Assemble recent conversation history into a structured, bounded prompt.
        Preserves newest messages without exceeding token/character limits.
        """
        formatted_history = []
        char_count = len(current_message)

        # Iterate in reverse (newest first) to ensure newest turns fit in context budget
        reversed_history = list(reversed(previous_messages))
        included_messages = []

        for msg in reversed_history:
            entry_len = len(msg.content) + 20
            if char_count + entry_len > MAX_CONTEXT_CHARACTERS:
                break
            char_count += entry_len
            included_messages.append(msg)

        # Restore chronological order
        for msg in reversed(included_messages):
            sender_label = "User" if msg.sender == "USER" else "CareAI Assistant"
            formatted_history.append(f"[{sender_label}]: {msg.content}")

        history_block = (
            "\n".join(formatted_history)
            if formatted_history
            else "(No prior messages in this conversation thread.)"
        )

        user_prompt = (
            f"=== CONVERSATION CONTEXT ===\n"
            f"Active User: {user_name}\n"
            f"Active User Role: {user_role.value}\n\n"
            f"=== PRIOR CONVERSATION HISTORY ===\n"
            f"{history_block}\n\n"
            f"=== CURRENT USER INQUIRY ===\n"
            f"[User]: {current_message}\n\n"
            f"[CareAI Assistant]:"
        )
        return user_prompt

    def send_chat_message(
        self,
        db: Session,
        user: User,
        request: AIChatRequest,
    ) -> AIChatResponse:
        """
        Execute an AI conversation turn:
        1. Validate conversation ownership or initialize new thread.
        2. Assemble bounded conversation context.
        3. Inject role-specific system prompt & medical safety guardrails.
        4. Call Gemini AI provider.
        5. Persist user & assistant messages in transactional database.
        """
        conversation: Optional[AIConversation] = None

        # 1. Resolve conversation thread
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
            db.flush()  # Populate conversation.id

        # 2. Fetch recent conversation messages for context
        prior_messages = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at.desc())
            .limit(MAX_CONTEXT_MESSAGES)
            .all()
        )
        # Sort chronologically for prompt assembly
        prior_messages.sort(key=lambda m: m.created_at)

        # 3. Retrieve role-specific system prompt & assemble bounded user prompt
        system_prompt = get_system_prompt_for_role(user.role)
        assembled_prompt = self._assemble_bounded_prompt(
            previous_messages=prior_messages,
            current_message=request.message,
            user_role=user.role,
            user_name=user.full_name,
        )

        # 4. Invoke Genuine Gemini Foundation Model via AIClient
        try:
            assistant_response_text = ai_client.generate_completion(
                system_prompt=system_prompt,
                user_prompt=assembled_prompt,
                response_mime_type="text/plain",
            )
        except AIProviderUnavailableError as exc:
            logger.error(f"AI Assistant provider outage: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CareAI Assistant is temporarily unavailable. Please try again in a few moments.",
            ) from exc
        except AIInvalidResponseError as exc:
            logger.error(f"AI Assistant received invalid output: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="CareAI Assistant received an empty or unparseable response from the AI provider.",
            ) from exc
        except Exception as exc:
            logger.error(f"Unexpected error during AI assistant execution: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CareAI Assistant encountered an unexpected error processing your request.",
            ) from exc

        # 5. Persist user turn and assistant response turn
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
            content=assistant_response_text.strip(),
            model_name=ai_client.model_name,
            created_at=now,
        )
        conversation.updated_at = now
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()

        # 6. Safety metadata evaluation
        safety_metadata = self._evaluate_safety_metadata(request.message)

        return AIChatResponse(
            conversation_id=conversation.id,
            assistant_response=assistant_response_text.strip(),
            role=user.role.value,
            model_name=ai_client.model_name,
            created_at=now,
            safety_metadata=safety_metadata,
        )

    def list_conversations(
        self,
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AIConversationSummary]:
        """Retrieve historical conversation summaries strictly owned by the authenticated user."""
        conversations = (
            db.query(AIConversation)
            .filter(AIConversation.user_id == user.id)
            .order_by(AIConversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        summaries: List[AIConversationSummary] = []
        for conv in conversations:
            count = (
                db.query(func.count(AIMessage.id))
                .filter(AIMessage.conversation_id == conv.id)
                .scalar()
                or 0
            )
            last_msg = (
                db.query(AIMessage)
                .filter(AIMessage.conversation_id == conv.id)
                .order_by(AIMessage.created_at.desc())
                .first()
            )
            preview = None
            if last_msg:
                preview = (
                    last_msg.content[:80] + "..."
                    if len(last_msg.content) > 80
                    else last_msg.content
                )

            summaries.append(
                AIConversationSummary(
                    id=conv.id,
                    user_id=conv.user_id,
                    role=conv.role,
                    title=conv.title,
                    message_count=count,
                    last_message_preview=preview,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                )
            )

        return summaries

    def get_conversation(
        self,
        db: Session,
        user: User,
        conversation_id: int,
    ) -> AIConversationRead:
        """Retrieve full conversation details and messages for an authorized thread."""
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )

        messages = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )

        return AIConversationRead(
            id=conversation.id,
            user_id=conversation.user_id,
            role=conversation.role,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[AIMessageRead.model_validate(m) for m in messages],
        )

    def delete_conversation(
        self,
        db: Session,
        user: User,
        conversation_id: int,
    ) -> bool:
        """Permanently delete a conversation and all cascaded message history."""
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )

        db.delete(conversation)
        db.commit()
        return True


ai_assistant_service = AIAssistantService()
