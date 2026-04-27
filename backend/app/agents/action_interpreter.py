"""
ActionInterpreter -- turns free-text user input into a structured Intent.

Never refuses. Nonsense gets plausibility <= 0.2 and a clarification question.
Single Groq JSON-mode call, temperature 0.2, max_tokens 220.
On failure -> safe fallback Intent(verb="clarify", plausibility=0.1).
"""
from __future__ import annotations

from pathlib import Path

import structlog

from app.agents.groq_helper import call_groq_json
from app.agents.schemas import Intent, ScenarioBriefData, UserAction

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "interpreter.system.md"

_FALLBACK_INTENT = Intent(
    verb="clarify",
    target="world.unknown",
    parameters={},
    plausibility=0.1,
    requires_clarification="Write what you want to do.",
    raw_paraphrase="Unclear input -- asking for clarification",
)


def _build_user_prompt(
    action: UserAction,
    brief: ScenarioBriefData,
    recent_history_summary: str,
) -> str:
    lines = [
        "## Scenario context",
        f"Profession: {brief.profession_slug}",
        f"Brief: {brief.title}",
        f"NPC: {brief.npc_definition.display_name} ({brief.npc_definition.role})",
        f"User locale: {action.locale}",
    ]
    if recent_history_summary:
        lines += ["", "## Recent turn summary", recent_history_summary]
    lines += ["", "## User input", action.raw_text]
    return "\n".join(lines)


def _parse_intent(data: dict) -> Intent:
    return Intent(
        verb=str(data.get("verb", "clarify")).lower().strip(),
        target=str(data.get("target", "world.unknown")).lower().strip(),
        parameters=dict(data.get("parameters") or {}),
        plausibility=max(0.0, min(1.0, float(data.get("plausibility", 0.5)))),
        requires_clarification=data.get("requires_clarification") or None,
        raw_paraphrase=str(data.get("raw_paraphrase", "")),
    )


class ActionInterpreter:

    async def interpret(
        self,
        action: UserAction,
        brief: ScenarioBriefData,
        recent_history_summary: str = "",
    ) -> Intent:
        system = _PROMPT_PATH.read_text(encoding="utf-8")
        user = _build_user_prompt(action, brief, recent_history_summary)
        try:
            data = await call_groq_json(
                system_prompt=system,
                user_prompt=user,
                max_tokens=220,
                temperature=0.2,
                schema_hint="Intent",
            )
            intent = _parse_intent(data)
            logger.info(
                "intent_parsed",
                verb=intent.verb,
                target=intent.target,
                plausibility=intent.plausibility,
            )
            return intent
        except Exception as e:
            logger.warning("interpreter_fallback", error=str(e))
            return _FALLBACK_INTENT
