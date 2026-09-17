"""Administrator AI Assistant Service providing mathematically grounded platform intelligence."""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.ai.base_ai_service import BaseAIService
from app.services.ai.context_retrieval import context_retrieval_service
from app.ai.assistant_prompts import ADMIN_ASSISTANT_PROMPT

logger = logging.getLogger("healthcare.ai.admin")


class AdminAIService(BaseAIService):
    """Admin-specific AI assistant utilizing verified parameterized database aggregations."""

    def __init__(self) -> None:
        super().__init__(role=UserRole.ADMIN)

    def _get_system_prompt(self) -> str:
        return f"""{ADMIN_ASSISTANT_PROMPT}

DATABASE GROUNDING INSTRUCTION:
- You have been provided with real, verified database counts and metrics in the section labeled 'AUTHORIZED LIVE DATABASE CONTEXT'.
- When the administrator asks for statistics (e.g. total users, patients, doctors, lab technicians, pharmacy staff, doctor approval status, appointments scheduled, prescriptions by status, or lab orders), you MUST cite the exact numbers from this context.
- Format statistics cleanly in markdown tables or bulleted executive breakdowns.
- NEVER invent, extrapolate, or guess platform metrics. If a metric is not present in the database context, state that it is currently unrecorded rather than fabricating a figure.
"""

    def _retrieve_live_context(self, db: Session, user: User, query: str) -> Dict[str, Any]:
        """Fetch real parameterized database counts across users, doctors, appointments, prescriptions, and labs."""
        return context_retrieval_service.get_admin_context(db)


admin_ai_service = AdminAIService()
