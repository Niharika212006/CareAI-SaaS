"""AI module exports."""
from app.ai.client import ai_client, AIClient
from app.ai.prompts import (
    PRESCRIPTION_SAFETY_SYSTEM_PROMPT,
    PRESCRIPTION_ANALYSIS_USER_TEMPLATE,
)
from app.ai.interaction_checker import interaction_checker, InteractionChecker

__all__ = [
    "ai_client",
    "AIClient",
    "PRESCRIPTION_SAFETY_SYSTEM_PROMPT",
    "PRESCRIPTION_ANALYSIS_USER_TEMPLATE",
    "interaction_checker",
    "InteractionChecker",
]
