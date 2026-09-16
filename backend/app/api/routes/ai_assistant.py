"""API route endpoints for the Centralized Role-Aware CareAI Assistant."""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.ai.client import ai_client
from app.schemas.ai_assistant import (
    AIChatRequest,
    AIChatResponse,
    AIConversationRead,
    AIConversationSummary,
    AIConfigRead,
    AIConfigUpdate,
)
from app.services.ai_assistant_service import ai_assistant_service

router = APIRouter(prefix="/ai-assistant", tags=["CareAI Assistant"])


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interact with the role-aware CareAI Assistant",
)
def chat_with_assistant(
    request: AIChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AIChatResponse:
    """
    Execute a conversational interaction turn with the CareAI Assistant.
    
    Security & RBAC Enforcement:
    - User identity and role are derived strictly from the authenticated JWT token.
    - System prompts and clinical safety guardrails adapt dynamically to the user's role:
      - PATIENT: Health education, medication/lab explanation, emergency symptom triage.
      - DOCTOR: Clinical copilot, authorized patient data and document synthesis.
      - LAB_TECHNICIAN: Laboratory testing protocols, diagnostic terminology, workflow guidance.
      - PHARMACY_STAFF: Drug interaction analysis, medication safety, formulary guidance.
      - ADMIN: Operational intelligence and governance with strict privacy barrier.
    """
    return ai_assistant_service.send_chat_message(
        db=db,
        user=current_user,
        request=request,
    )


@router.get(
    "/conversations",
    response_model=List[AIConversationSummary],
    summary="List all assistant conversation threads for authenticated user",
)
def list_my_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[AIConversationSummary]:
    """Retrieve historical assistant conversation threads belonging to the authenticated user."""
    return ai_assistant_service.list_conversations(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=AIConversationRead,
    summary="Retrieve full conversation thread and message history",
)
def get_conversation_history(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AIConversationRead:
    """Retrieve complete message history for an authorized conversation thread."""
    return ai_assistant_service.get_conversation(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=Dict[str, Any],
    summary="Delete an assistant conversation thread",
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Permanently delete an assistant conversation thread and its associated messages."""
    ai_assistant_service.delete_conversation(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
    )
    return {
        "status": "success",
        "message": f"Conversation {conversation_id} deleted successfully.",
        "id": conversation_id,
    }


@router.get(
    "/config",
    response_model=AIConfigRead,
    summary="Retrieve current AI provider and engine status",
)
def get_ai_config(
    current_user: User = Depends(get_current_active_user),
) -> AIConfigRead:
    """Retrieve operational status and active engine (Gemini vs Clinical Knowledge Engine)."""
    status_data = ai_client.get_status()
    return AIConfigRead(**status_data)


@router.post(
    "/config",
    response_model=Dict[str, Any],
    summary="Configure or update Gemini API key at runtime",
)
def update_ai_config(
    payload: AIConfigUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Set or clear Gemini API key dynamically.
    Enables live Google Gemini foundation model processing.
    """
    key = payload.api_key.strip()
    ai_client.set_gemini_key(key)

    # Try updating backend/.env file so key persists across server restarts
    try:
        from pathlib import Path
        import re
        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            if "GEMINI_API_KEY=" in content:
                new_content = re.sub(r'GEMINI_API_KEY="[^"]*"', f'GEMINI_API_KEY="{key}"', content)
                if new_content == content:
                    new_content = re.sub(r"GEMINI_API_KEY=.*", f'GEMINI_API_KEY="{key}"', content)
                env_path.write_text(new_content, encoding="utf-8")
    except Exception:
        pass

    status_data = ai_client.get_status()
    return {
        "status": "success",
        "message": "Gemini API key updated successfully." if key else "Reset to CareAI Clinical Intelligence Engine.",
        "config": status_data,
    }

