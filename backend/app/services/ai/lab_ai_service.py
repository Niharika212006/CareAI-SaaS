"""Laboratory Technician AI Assistant Service supporting diagnostic workflows and quality control."""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.ai.base_ai_service import BaseAIService
from app.services.ai.context_retrieval import context_retrieval_service
from app.ai.assistant_prompts import LAB_TECHNICIAN_ASSISTANT_PROMPT

logger = logging.getLogger("healthcare.ai.lab")


class LabAIService(BaseAIService):
    """Lab Technician AI assistant grounded in laboratory queue and diagnostic test statuses."""

    def __init__(self) -> None:
        super().__init__(role=UserRole.LAB_TECHNICIAN)

    def _get_system_prompt(self) -> str:
        return f"""{LAB_TECHNICIAN_ASSISTANT_PROMPT}

LABORATORY WORKFLOW GROUNDING INSTRUCTIONS:
- You have access to the diagnostic laboratory's live order queue, specimen collection backlog, pending verification orders, and critical panic alerts under 'AUTHORIZED LIVE DATABASE CONTEXT'.
- When the laboratory technician asks:
  * "How many lab orders are pending?" -> Cite the exact count of orders in `SAMPLE_PENDING` and other active stages from the database context.
  * "Which samples are awaiting processing?" -> Detail specimens pending collection or accessioning.
  * "Which results are waiting for verification?" -> List orders in `RESULTS_ENTERED` status awaiting technician review.
  * "Explain specimen rejection criteria" -> Detail pre-analytical rejection guidelines for hemolyzed, clotted, or insufficient specimens.
  * "Critical panic alerts" -> Detail recently flagged panic values requiring immediate telephone read-back escalation to attending physicians.
- OPERATIONAL BOUNDARY: The AI cannot independently approve, modify, or release laboratory results. Critical clinical decisions must remain with certified laboratory professionals.
"""

    def _retrieve_live_context(self, db: Session, user: User, query: str) -> Dict[str, Any]:
        """Fetch the diagnostic laboratory order queue and workflow statuses."""
        return context_retrieval_service.get_lab_context(db, user)


lab_ai_service = LabAIService()
