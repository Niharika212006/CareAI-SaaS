"""Clinical Safety and Medical Risk Screening Service for CareAI.

Ensures real-time detection of emergency symptoms, patient risk triage,
and mandatory healthcare disclaimer attachment across all AI touchpoints.
"""
import re
from typing import Dict, Any, Optional
from app.models.user import UserRole


# Critical emergency red-flag patterns requiring immediate escalation
EMERGENCY_PATTERNS = [
    r"\bchest pain\b",
    r"\bpressure in chest\b",
    r"\bheart attack\b",
    r"\bshortness of breath\b",
    r"\bcan'?t breathe\b",
    r"\bcannot breathe\b",
    r"\bdifficulty breathing\b",
    r"\bstruggling to breathe\b",
    r"\bslurred speech\b",
    r"\bcannot speak\b",
    r"\bcan'?t speak\b",
    r"\bfacial droop(?:ing)?\b",
    r"\barm weakness\b",
    r"\bnumbness\b",
    r"\bstroke\b",
    r"\bunconscious\b",
    r"\bpassed out\b",
    r"\bsevere bleeding\b",
    r"\bcoughing up blood\b",
    r"\banaphylaxis\b",
    r"\bthroat closing\b",
    r"\bswelling of lips or tongue\b",
    r"\boverdose\b",
    r"\bpoison(?:ing)?\b",
    r"\bsuicid(?:e|al)\b",
    r"\bwant to die\b",
    r"\bself[\s-]harm\b",
    r"\bseizure\b",
]

EMERGENCY_NOTICE = (
    "🚨 **EMERGENCY MEDICAL WARNING:** Your inquiry may indicate an acute, life-threatening emergency. "
    "Please **immediately call local emergency services (e.g. 911 / 112 / 108)** or proceed to the nearest emergency department. "
    "Do not delay urgent emergency care to read online information."
)


class SafetyService:
    """Evaluates clinical safety, emergency triggers, and responsible AI guardrails."""

    def evaluate_emergency_symptoms(self, message: str) -> Dict[str, Any]:
        """Detect acute red-flag symptoms and return triage safety guidance."""
        lower_msg = message.lower()
        for pattern in EMERGENCY_PATTERNS:
            if re.search(pattern, lower_msg):
                return {
                    "emergency_symptom_detected": True,
                    "triage_guidance": EMERGENCY_NOTICE,
                }
        return {"emergency_symptom_detected": False}

    def detect_emergency_symptoms(self, message: str) -> tuple:
        """Helper returning tuple: (is_emergency: bool, triage_banner: str)."""
        res = self.evaluate_emergency_symptoms(message)
        if res.get("emergency_symptom_detected"):
            return True, res.get("triage_guidance", EMERGENCY_NOTICE)
        return False, ""

    def get_role_disclaimer(self, role: UserRole) -> str:
        """Provide official medical disclaimer tailored to user's clinical authority."""
        if role == UserRole.PATIENT:
            return (
                "\n\n---\n*Important Medical Notice: CareAI provides health education and informational guidance only. "
                "It is not a substitute for professional medical diagnosis, advice, or treatment. Always verify all medication "
                "instructions and health concerns with your prescribing doctor.*"
            )
        elif role == UserRole.DOCTOR:
            return (
                "\n\n---\n*Clinical Decision Support Notice: CareAI assists with authorized documentation and evidence-based "
                "synthesis. It does not replace independent clinical evaluation or institutional protocols.*"
            )
        elif role == UserRole.LAB_TECHNICIAN:
            return (
                "\n\n---\n*Laboratory Guidance Notice: Standard operating protocols (CLIA/CAP) govern diagnostic testing. "
                "Clinical result authorization and critical panic notifications must be verified by a licensed laboratory professional.*"
            )
        elif role == UserRole.PHARMACY_STAFF:
            return (
                "\n\n---\n*Pharmacy Practice Notice: Medication dispensing must comply with authorized doctor prescriptions and "
                "pharmacy licensing regulations. Do not alter active prescriptions without direct prescriber authorization.*"
            )
        elif role == UserRole.ADMIN:
            return (
                "\n\n---\n*Platform Governance Notice: Metrics reflect live authorized database statistics under strict "
                "Role-Based Access Control and HIPAA privacy boundaries.*"
            )
        return ""


safety_service = SafetyService()
