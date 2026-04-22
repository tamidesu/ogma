import json
import re
import time
from typing import AsyncGenerator

import structlog
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.provider_adapter import AIProvider, FeedbackResult, StructuredFeedback
from app.config import settings
from app.core.exceptions import AIProviderError

logger = structlog.get_logger(__name__)

PROMPT_VERSION = "v2.0"

# Models that support JSON mode on Groq
_JSON_MODE_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
}

_FALLBACK_STRUCTURED = StructuredFeedback(
    feedback="Unable to generate feedback at this time.",
    key_insight="Keep reflecting on your decisions.",
    coaching_question="What would you do differently next time?",
    consequence_analysis="Continue making decisions to see your progress.",
    tone="neutral",
)


def _parse_structured_response(raw: str) -> StructuredFeedback:
    """Parse JSON response from LLM. Falls back gracefully on any parse error."""
    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        data = json.loads(clean)
        return StructuredFeedback(
            feedback=str(data.get("feedback", raw[:500])),
            key_insight=str(data.get("key_insight", "")),
            coaching_question=str(data.get("coaching_question", "")),
            consequence_analysis=str(data.get("consequence_analysis", "")),
            tone=str(data.get("tone", "neutral")),
            alternative_path=str(data.get("alternative_path", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("json_parse_failed", raw_preview=raw[:200])
        # Treat the entire response as plain feedback text
        return StructuredFeedback(
            feedback=raw[:600],
            key_insight="",
            coaching_question="",
            consequence_analysis="",
            tone="neutral",
        )


class GroqAdapter(AIProvider):

    def __init__(self):
        self._client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=settings.groq_timeout,
        )
        self._model = settings.groq_default_model
        self._fallback_model = settings.groq_fallback_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        reraise=True,
    )
    async def generate_feedback(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 700,
    ) -> FeedbackResult:
        start = time.monotonic()
        model = self._model
        use_json = settings.ai_structured_output and model in _JSON_MODE_MODELS

        kwargs: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": settings.groq_temperature,
        }
        if use_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.chat.completions.create(**kwargs)
            raw = response.choices[0].message.content or ""
        except Exception as e:
            logger.warning("groq_primary_failed", error=str(e), model=model)
            # Retry with fallback model
            model = self._fallback_model
            kwargs["model"] = model
            use_json = settings.ai_structured_output and model in _JSON_MODE_MODELS
            if use_json:
                kwargs["response_format"] = {"type": "json_object"}
            else:
                kwargs.pop("response_format", None)
            try:
                response = await self._client.chat.completions.create(**kwargs)
                raw = response.choices[0].message.content or ""
            except Exception as fallback_err:
                raise AIProviderError(f"AI provider unavailable: {fallback_err}") from fallback_err

        latency_ms = int((time.monotonic() - start) * 1000)

        structured = _parse_structured_response(raw) if use_json else StructuredFeedback(
            feedback=raw[:600],
            key_insight="",
            coaching_question="",
            consequence_analysis="",
            tone="neutral",
        )

        logger.info(
            "groq_feedback_generated",
            model=model,
            latency_ms=latency_ms,
            tone=structured.tone,
            json_mode=use_json,
        )
        return FeedbackResult(
            structured=structured,
            model=model,
            prompt_version=PROMPT_VERSION,
            latency_ms=latency_ms,
            raw_text=raw,
        )

    async def generate_feedback_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 700,
    ) -> AsyncGenerator[str, None]:
        """Yield text chunks as they arrive from Groq."""
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=settings.groq_temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def health_check(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self._fallback_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=3,
            )
            return True
        except Exception:
            return False
