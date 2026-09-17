"""Patient AI Assistant Service providing personalized, safe, and plain-language health guidance."""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.ai.base_ai_service import BaseAIService
from app.services.ai.context_retrieval import context_retrieval_service
from app.ai.assistant_prompts import PATIENT_ASSISTANT_PROMPT

logger = logging.getLogger("healthcare.ai.patient")


class PatientAIService(BaseAIService):
    """Patient AI assistant grounded in authorized prescriptions, appointments, and diagnostic records."""

    def __init__(self) -> None:
        super().__init__(role=UserRole.PATIENT)

    def _get_system_prompt(self) -> str:
        return f"""{PATIENT_ASSISTANT_PROMPT}

PATIENT DATA GROUNDING & SAFETY INSTRUCTIONS:
- You have access to the authenticated patient's verified active prescriptions, upcoming appointments, and released lab reports under 'AUTHORIZED LIVE DATABASE CONTEXT'.
- When the patient asks:
  * "What medicines did my doctor prescribe?" -> List the exact medication names, dosages, frequencies, duration, and instructions from their verified prescriptions.
  * "What appointments do I have?" -> Summarize scheduled appointment dates, times, and physician names.
  * "What lab reports are available?" -> Summarize their completed diagnostic test panels.
  * "Help me navigate the portal" -> Explain how to access appointments, prescriptions, and medical records from the dashboard.
- MEDICAL SAFETY RULES:
  * NEVER alter, increase, or decrease a medication dosage.
  * NEVER prescribe a medication or advise a patient to stop a prescription without doctor consultation.
  * If a prescription lacks specific timing instructions, explain the recorded directions and advise confirming timing with their doctor or pharmacist.
  * Translate complex medical terminology into clear, accessible language.
"""

    def _retrieve_live_context(self, db: Session, user: User, query: str) -> Dict[str, Any]:
        """Fetch the patient's verified prescriptions, appointments, and released lab reports."""
        return context_retrieval_service.get_patient_context(db, user)


patient_ai_service = PatientAIService()
