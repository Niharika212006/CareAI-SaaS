"""Gemini AI Provider integration with multi-model fallback and deterministic clinical handover."""
import logging
from typing import Optional, Dict, Any
from app.ai.client import ai_client, AIProviderUnavailableError, AIInvalidResponseError

logger = logging.getLogger("healthcare.ai.provider")


class GeminiProvider:
    """Manages LLM generation with robust error handling, rate-limit tolerance, and engine fallback."""

    def is_live_configured(self) -> bool:
        """Check if live LLM credentials are actively configured."""
        return ai_client.is_configured()

    @property
    def model_name(self) -> str:
        return ai_client.model_name

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_mime_type: str = "text/plain",
    ) -> str:
        """
        Execute completion with multi-tier fallback:
        1. Google Gemini (configured model -> candidate fallbacks)
        2. Seamless fallback to deterministic CareAI Clinical Intelligence Engine
        """
        try:
            return ai_client.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_mime_type=response_mime_type,
            )
        except AIInvalidResponseError:
            logger.warning("Empty response from primary model; executing clinical fallback.")
            return ai_client._generate_clinical_engine_response(system_prompt, user_prompt, response_mime_type)
        except Exception as err:
            logger.warning(f"AI Provider issue ({err}); generating response via CareAI Clinical Engine.")
            return ai_client._generate_clinical_engine_response(system_prompt, user_prompt, response_mime_type)


gemini_provider = GeminiProvider()
