"""
Shared Groq JSON-mode helper for all agents.

Every agent in app/agents/ uses the same pattern:
  - JSON mode on, small max_tokens, tenacity retry on bad JSON.
  - On second failure returns a safe fallback dict (caller converts to schema).

Usage:
    result = await call_groq_json(
        system_prompt=...,
        user_prompt=...,
        max_tokens=200,
        temperature=0.2,
        schema_hint="Intent",   # for log context only
    )
"""
from __future__ import annotations

import json
import re
import time

import structlog
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger(__name__)

# Models that support JSON mode on Groq
_JSON_MODE_MODELS = frozenset({
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
})

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key, timeout=settings.groq_timeout)
    return _client


def _strip_fences(raw: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    return re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()


async def call_groq_json(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 400,
    temperature: float = 0.3,
    schema_hint: str = "unknown",
) -> dict:
    """
    Call Groq in JSON mode. Retries once on invalid JSON.
    Raises AIProviderError if both attempts fail.
    Returns a parsed dict on success.
    """
    model = settings.groq_default_model
    use_json = model in _JSON_MODE_MODELS

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if use_json:
        kwargs["response_format"] = {"type": "json_object"}

    start = time.monotonic()
    raw = ""
    last_err: Exception | None = None

    # Two attempts: primary model, then fallback model
    for attempt_model in (model, settings.groq_fallback_model):
        kwargs["model"] = attempt_model
        if attempt_model in _JSON_MODE_MODELS:
            kwargs["response_format"] = {"type": "json_object"}
        else:
            kwargs.pop("response_format", None)
        try:
            resp = await _get_client().chat.completions.create(**kwargs)
            raw = (resp.choices[0].message.content or "").strip()
            cleaned = _strip_fences(raw)
            result = json.loads(cleaned)
            latency = int((time.monotonic() - start) * 1000)
            logger.debug(
                "groq_json_ok",
                schema=schema_hint,
                model=attempt_model,
                latency_ms=latency,
            )
            return result
        except json.JSONDecodeError as e:
            last_err = e
            logger.warning(
                "groq_json_parse_failed",
                schema=schema_hint,
                model=attempt_model,
                raw_preview=raw[:200],
                error=str(e),
            )
            # Try the fallback model on next loop iteration
            continue
        except Exception as e:
            last_err = e
            logger.warning(
                "groq_call_failed",
                schema=schema_hint,
                model=attempt_model,
                error=str(e),
            )
            continue

    from app.core.exceptions import AIProviderError
    raise AIProviderError(
        f"groq_json failed for schema={schema_hint} after 2 attempts: {last_err}"
    )


async def call_groq_stream(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 600,
    temperature: float = 0.7,
):
    """Yield text chunks — used by MentorCoach for streamed feedback."""
    stream = await _get_client().chat.completions.create(
        model=settings.groq_default_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
