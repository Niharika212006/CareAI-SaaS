"""Pharmacy Staff AI Assistant Service supporting prescription review and medication safety."""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.ai.base_ai_service import BaseAIService
from app.services.ai.context_retrieval import context_retrieval_service
from app.ai.assistant_prompts import PHARMACY_STAFF_ASSISTANT_PROMPT

logger = logging.getLogger("healthcare.ai.pharmacy")


class PharmacyAIService(BaseAIService):
    """Pharmacy Staff AI assistant grounded in dispensary queue and prescription statuses."""

    def __init__(self) -> None:
        super().__init__(role=UserRole.PHARMACY_STAFF)

    def _get_system_prompt(self) -> str:
        return f"""{PHARMACY_STAFF_ASSISTANT_PROMPT}

DISPENSARY WORKFLOW GROUNDING INSTRUCTIONS:
- You have access to the dispensary's live prescription queue, breakdown across fulfillment stages (`PRESCRIBED`, `UNDER_REVIEW`, `READY`, `DISPENSED`), and orders awaiting pharmacist review under 'AUTHORIZED LIVE DATABASE CONTEXT'.
- When pharmacy personnel ask:
  * "How many prescriptions are pending?" -> Provide exact counts from the database context for each stage.
  * "Which prescriptions are under review?" -> List pending prescriptions awaiting pharmacist clinical evaluation.
  * "How many are ready for dispensing?" -> List prescriptions in `READY` status awaiting patient pickup.
  * "Screen drug interactions" -> Analyze medication regimens for CYP450 metabolism conflicts, food timing restrictions, and black box warnings.
- OPERATIONAL BOUNDARY: The AI cannot independently dispense medications or authorize off-label prescription modifications. Prescriptions are legally immutable without physician consultation.
"""

    def _retrieve_live_context(self, db: Session, user: User, query: str) -> Dict[str, Any]:
        """Fetch the dispensary prescription queue and fulfillment statuses."""
        return context_retrieval_service.get_pharmacy_context(db, user)


pharmacy_ai_service = PharmacyAIService()
