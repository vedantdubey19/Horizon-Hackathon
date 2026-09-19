"""Provider-agnostic LLM client for MarkLoss.

Defaults to Gemini using google-genai SDK, configurable via environment.
Supports vision and text JSON generation with timeouts and retries.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from app.config import settings
from app.errors import InvalidModelOutputError, LLMUnavailableError

logger = logging.getLogger("markloss.llm")

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Abstract interface for LLM operations."""

    async def generate_vision_json(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    async def generate_text_json(
        self,
        prompt: str,
        system_instruction: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        raise NotImplementedError


def _clean_json_text(text: str) -> str:
    """Clean markdown code fences from JSON text before parsing."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


class GeminiLLMClient(LLMClient):
    """Google Gemini LLM client implementation."""

    def __init__(self):
        self.api_key = settings.api_key
        self.vision_model = settings.LLM_MODEL_VISION
        self.text_model = settings.LLM_MODEL_TEXT
        self.timeout = settings.TIMEOUT_SECONDS
        self._client = None

    def _get_client(self):
        current_key = settings.api_key
        if self._client is None or self.api_key != current_key:
            from google import genai

            self.api_key = current_key
            if not self.api_key:
                raise LLMUnavailableError(
                    detail="LLM_API_KEY / GEMINI_API_KEY is not configured in backend environment."
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def _execute_with_timeout(self, func, *args, **kwargs):
        """Run synchronous genai call in threadpool with strict timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            logger.error("LLM call timed out after %s seconds", self.timeout)
            raise LLMUnavailableError(
                detail=f"AI model call timed out after {self.timeout}s."
            )
        except Exception as e:
            err_msg = str(e)
            logger.error("LLM call failed: %s", err_msg)
            raise LLMUnavailableError(detail=err_msg)

    async def generate_vision_json(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        from google.genai import types

        client = self._get_client()
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ]
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
        )

        t0 = time.time()
        for attempt in range(2):  # 1 initial + 1 retry
            try:
                response = await self._execute_with_timeout(
                    client.models.generate_content,
                    model=self.vision_model,
                    contents=contents,
                    config=config,
                )
                duration = time.time() - t0
                logger.info(
                    "Vision LLM call succeeded (model=%s, attempt=%d, duration=%.2fs)",
                    self.vision_model,
                    attempt + 1,
                    duration,
                )

                raw_text = response.text or "{}"
                cleaned_text = _clean_json_text(raw_text)
                data = json.loads(cleaned_text)

                if response_model:
                    validated = response_model.model_validate(data)
                    return validated.model_dump()
                return data

            except json.JSONDecodeError as jde:
                if attempt == 0:
                    logger.warning("JSON decode failed on attempt 1, retrying...")
                    continue
                raise InvalidModelOutputError(
                    detail=f"Failed to parse model JSON: {str(jde)}"
                )
            except LLMUnavailableError:
                raise
            except Exception as e:
                if attempt == 0:
                    logger.warning("Vision generation failed on attempt 1, retrying: %s", str(e))
                    continue
                raise InvalidModelOutputError(detail=str(e))

        raise InvalidModelOutputError(detail="Exhausted generation attempts.")

    async def generate_text_json(
        self,
        prompt: str,
        system_instruction: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        from google.genai import types

        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
        )

        t0 = time.time()
        for attempt in range(2):
            try:
                response = await self._execute_with_timeout(
                    client.models.generate_content,
                    model=self.text_model,
                    contents=prompt,
                    config=config,
                )
                duration = time.time() - t0
                logger.info(
                    "Text LLM call succeeded (model=%s, attempt=%d, duration=%.2fs)",
                    self.text_model,
                    attempt + 1,
                    duration,
                )

                raw_text = response.text or "{}"
                cleaned_text = _clean_json_text(raw_text)
                data = json.loads(cleaned_text)

                if response_model:
                    validated = response_model.model_validate(data)
                    return validated.model_dump()
                return data

            except json.JSONDecodeError as jde:
                if attempt == 0:
                    logger.warning("JSON decode failed on attempt 1, retrying...")
                    continue
                raise InvalidModelOutputError(
                    detail=f"Failed to parse text model JSON: {str(jde)}"
                )
            except LLMUnavailableError:
                raise
            except Exception as e:
                if attempt == 0:
                    logger.warning("Text generation failed on attempt 1, retrying: %s", str(e))
                    continue
                raise InvalidModelOutputError(detail=str(e))

        raise InvalidModelOutputError(detail="Exhausted generation attempts.")


_CLIENT_INSTANCE: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Factory to retrieve singleton LLM client."""
    global _CLIENT_INSTANCE
    if _CLIENT_INSTANCE is None:
        if settings.LLM_PROVIDER.lower() == "gemini":
            _CLIENT_INSTANCE = GeminiLLMClient()
        else:
            # Fallback to Gemini
            _CLIENT_INSTANCE = GeminiLLMClient()
    return _CLIENT_INSTANCE


def set_llm_client(client: Optional[LLMClient]) -> None:
    """Override LLM client (useful for unit testing and mocking)."""
    global _CLIENT_INSTANCE
    _CLIENT_INSTANCE = client
