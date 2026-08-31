"""Modular AI Client integrating official Google GenAI and external LLM providers."""
import os
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("healthcare.ai.client")


class AIProviderUnavailableError(Exception):
    """Raised when the requested AI provider is unconfigured, unreachable, or timed out."""
    pass


class AIInvalidResponseError(Exception):
    """Raised when the AI model returns empty, malformed, or unparseable output."""
    pass


class AIClient:
    """Interface for invoking Large Language Models for clinical reasoning and document analysis."""

    def __init__(self) -> None:
        self.provider = (settings.AI_PROVIDER or "gemini").lower()

    def _get_gemini_key(self) -> str:
        key = (
            settings.GEMINI_API_KEY
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GOOGLE_GENAI_API_KEY")
            or ""
        ).strip()
        if not key or key.startswith("your-") or "placeholder" in key.lower():
            return ""
        return key

    def _get_openai_key(self) -> str:
        key = (
            settings.OPENAI_API_KEY
            or os.getenv("OPENAI_API_KEY")
            or ""
        ).strip()
        if not key or key.startswith("your-") or "placeholder" in key.lower():
            return ""
        return key

    def _get_model_name(self) -> str:
        return (
            os.getenv("AI_MODEL_NAME")
            or settings.AI_MODEL_NAME
            or "gemini-1.5-flash"
        ).strip()

    @property
    def model_name(self) -> str:
        return self._get_model_name()

    def is_configured(self) -> bool:
        """Check if active credentials exist for the configured AI provider."""
        provider = (os.getenv("AI_PROVIDER") or settings.AI_PROVIDER or "gemini").lower()
        if provider == "gemini":
            return bool(self._get_gemini_key())
        elif provider == "openai":
            return bool(self._get_openai_key())
        return False

    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_mime_type: str = "application/json",
    ) -> str:
        """
        Generate structured response from the configured foundation LLM provider.
        Raises AIProviderUnavailableError if credentials are missing or the API call fails.
        Raises AIInvalidResponseError if output is empty.
        """
        provider = (os.getenv("AI_PROVIDER") or settings.AI_PROVIDER or "gemini").lower()

        if not self.is_configured():
            logger.warning(
                f"AI Provider '{provider}' is active but no valid API key is configured in environment."
            )
            raise AIProviderUnavailableError(
                f"AI analysis provider '{provider}' is not configured on the server."
            )

        if provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt, response_mime_type)
        elif provider == "openai":
            return self._call_openai(system_prompt, user_prompt, response_mime_type)
        else:
            raise AIProviderUnavailableError(f"Unsupported AI provider: {provider}")

    def _call_gemini(self, system_prompt: str, user_prompt: str, response_mime_type: str) -> str:
        """Execute real API call using the official Google GenAI SDK."""
        key = self._get_gemini_key()
        model = self._get_model_name()
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)
            
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type=response_mime_type,
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )

            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config,
            )

            if not response or not response.text:
                raise AIInvalidResponseError("Empty response returned by Gemini model.")

            return response.text.strip()

        except AIInvalidResponseError:
            raise
        except Exception as err:
            logger.error(f"Gemini API execution failure on model '{model}': {err}")
            raise AIProviderUnavailableError(
                f"Gemini AI provider is currently unreachable or encountered an error on model '{model}'."
            ) from err

    def _call_openai(self, system_prompt: str, user_prompt: str, response_mime_type: str) -> str:
        """Execute API call to OpenAI provider."""
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name if "gpt" in self.model_name else "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            }
            if response_mime_type == "application/json":
                payload["response_format"] = {"type": "json_object"}

            with httpx.Client(timeout=30.0) as http_client:
                res = http_client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if res.status_code != 200:
                    raise AIProviderUnavailableError(f"OpenAI error status: {res.status_code}")
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                if not content:
                    raise AIInvalidResponseError("Empty response from OpenAI.")
                return content.strip()

        except (AIProviderUnavailableError, AIInvalidResponseError):
            raise
        except Exception as err:
            logger.error(f"OpenAI API execution failure: {err}")
            raise AIProviderUnavailableError("OpenAI provider is currently unreachable.") from err


ai_client = AIClient()
