"""Doctor AI Clinical Copilot Service assisting physicians with clinical documentation and decision support."""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.ai.base_ai_service import BaseAIService
from app.services.ai.context_retrieval import context_retrieval_service
from app.ai.assistant_prompts import DOCTOR_ASSISTANT_PROMPT

logger = logging.getLogger("healthcare.ai.doctor")


class DoctorAIService(BaseAIService):
    """Doctor AI clinical copilot grounded in authorized schedules, patient encounters, and lab orders."""

    def __init__(self) -> None:
        super().__init__(role=UserRole.DOCTOR)

    def _get_system_prompt(self) -> str:
        return f"""{DOCTOR_ASSISTANT_PROMPT}

CLINICAL PRACTICE GROUNDING & DECISION SUPPORT:
- You have access to the physician's authorized consultation schedule, today's appointments, upcoming bookings, and recent diagnostic lab orders under 'AUTHORIZED LIVE DATABASE CONTEXT'.
- When the doctor asks:
  * "Show today's appointments" -> Summarize scheduled patient consultations with times, patient names, and reasons for visit.
  * "What lab orders are pending?" -> List diagnostic requisitions placed by this practice and their current workflow status.
  * "Screen drug interactions" -> Analyze drug combinations for contraindications, pharmacodynamic overlap, and severity grading.
  * "Prepare consultation summary" -> Draft a structured clinical encounter summary (Subjective, Objective, Assessment, Plan).
- All AI recommendations are advisory and designed to augment clinical workflow without superseding independent physician judgment.
"""

    def _retrieve_live_context(self, db: Session, user: User, query: str) -> Dict[str, Any]:
        """Fetch the doctor's consultation schedule and practice workflow records."""
        return context_retrieval_service.get_doctor_context(db, user, query)


doctor_ai_service = DoctorAIService()
