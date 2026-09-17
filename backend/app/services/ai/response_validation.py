"""Response validation and output sanitization layer for CareAI."""
import re
from typing import Dict, Any
from app.models.user import UserRole
from app.services.ai.safety_service import safety_service, EMERGENCY_NOTICE


class ResponseValidationService:
    """Validates and sanitizes AI output before delivering to users."""

    def validate_and_format(
        self,
        raw_response: str,
        role: UserRole,
        emergency_detected: bool,
    ) -> str:
        """
        Ensure responses are medically responsible:
        1. Prepend emergency warning banner if acute symptoms detected.
        2. Prevent illegal autonomous prescription claims.
        3. Append mandatory role disclaimer if missing.
        """
        cleaned = raw_response.strip()

        # Sanitize any hallucinated authoritative changes to prescriptions
        hallucination_patterns = [
            r"\bi have changed your (?:dosage|prescription)\b",
            r"\bi hereby (?:prescribe|alter|cancel) your\b",
            r"\bi confirm this diagnosis as definitive\b",
        ]
        for pattern in hallucination_patterns:
            cleaned = re.sub(
                pattern,
                "Please consult your prescribing doctor regarding any changes to your prescription",
                cleaned,
                flags=re.IGNORECASE,
            )

        # Prepend emergency warning banner if acute red-flag detected
        if emergency_detected and "EMERGENCY MEDICAL WARNING" not in cleaned:
            cleaned = f"{EMERGENCY_NOTICE}\n\n{cleaned}"

        # Append role disclaimer if not already present
        disclaimer = safety_service.get_role_disclaimer(role)
        if disclaimer and "Notice:" not in cleaned:
            cleaned = f"{cleaned}{disclaimer}"

        return cleaned


response_validator = ResponseValidationService()
