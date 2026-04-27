"""
MentorCoach — generates post-turn coaching feedback using the existing persona system.

Builds a concise prompt from the TurnResult (intent, validation verdict,
world delta, NPC reaction) and writes an AIFeedback row — same schema as
the legacy flow so the existing FeedbackDrawer component still works.
Runs as a BackgroundTask; exceptions are swallowed and logged.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.agents.groq_helper import call_groq_json
from app.agents.schemas import ScenarioBriefData, TurnResult

logger = structlog.get_logger(__name__)


_SYSTEM_TMPL = """{persona}

You are coaching a trainee after ONE turn of an open-world simulation.
You receive the action they took, the domain verdict, the NPC's reaction, and
the world-state changes that resulted. Write a tight 3-4 sentence coaching note.

Return JSON only:
{{
  "feedback": "<3-4 sentences in the user locale>",
  "key_insight": "<one sentence>",
  "coaching_question": "<one question for reflection, in user locale>",
  "consequence_analysis": "<one sentence on what changed in the world>",
  "alternative_path": "<one sentence — what else could they have done>",
  "tone": "encouraging | critical | neutral"
}}
"""

_PERSONAS = {
    "doctor": (
        "You are Dr. Zarina Bekova — a consultant physician and clinical educator with 20 years "
        "at a teaching hospital in Almaty. You are honest, direct, and warm. You give feedback "
        "as a trusted senior colleague, not a lecturer. You cite real protocols when relevant "
        "and acknowledge uncertainty where it exists."
    ),
    "lawyer": (
        "You are Aigerim Sultanova — a senior partner at a Kazakh law firm, experienced in "
        "litigation and legal education. You are precise, fair, and practical in your feedback."
    ),
    "software_engineer": (
        "You are Arman Seitkali — a staff engineer with 15 years of distributed systems experience. "
        "Blunt, constructive, focused on the real-world consequences of technical decisions."
    ),
    "business_manager": (
        "You are Damir Orazov — a seasoned business manager who has run teams across industries. "
        "You focus on strategy, stakeholder impact, and decision quality under uncertainty."
    ),
}


def _build_system(profession_slug: str) -> str:
    persona = _PERSONAS.get(profession_slug, _PERSONAS["doctor"])
    return _SYSTEM_TMPL.format(persona=persona)


def _build_user(
    turn: TurnResult,
    brief: ScenarioBriefData,
    user_input: str,
    turn_index: int,
) -> str:
    return "\n".join([
        f"## Turn {turn_index + 1} — {brief.title}",
        f"User action (raw): {user_input}",
        f"Intent: {turn.intent.verb} -> {turn.intent.target} (plausibility {turn.intent.plausibility:.2f})",
        f"Validation: SoC={turn.validation.is_standard_of_care}, "
        f"severity={turn.validation.severity_if_wrong}, "
        f"blocked={turn.validation.blocks_action}",
        f"Coach note from validator: {turn.validation.coach_note}",
        f"NPC reaction ({brief.npc_definition.display_name}): {turn.npc_update.utterance!r}",
        f"NPC state label: {turn.npc_update.new_state_label}",
        f"World changes: metrics={json.dumps(turn.world_delta.metric_delta, ensure_ascii=False)}, "
        f"time +{turn.world_delta.time_advance_min} min",
        f"Locale: {brief.locale}",
    ])


class MentorCoach:

    async def generate(
        self,
        turn: TurnResult,
        brief: ScenarioBriefData,
        session_id: UUID,
        turn_index: int,
        user_input: str,
        db=None,
    ) -> UUID | None:
        """
        Generate and persist an AIFeedback row. Returns the row's UUID on success.
        Exceptions are caught and logged — caller continues whether or not this
        succeeds (non-blocking background task).
        """
        try:
            system = _build_system(brief.profession_slug)
            user = _build_user(turn, brief, user_input, turn_index)

            data = await call_groq_json(
                system_prompt=system,
                user_prompt=user,
                max_tokens=600,
                temperature=0.65,
                schema_hint="MentorFeedback",
            )

            feedback_text = str(data.get("feedback", ""))
            key_insight = str(data.get("key_insight", ""))
            coaching_question = str(data.get("coaching_question", ""))
            consequence_analysis = str(data.get("consequence_analysis", ""))
            alternative_path = str(data.get("alternative_path", ""))
            tone = str(data.get("tone", "neutral"))

            if db is None:
                logger.info("mentor_coach_no_db", session_id=str(session_id))
                return None

            from app.db.models.ai_feedback import AIFeedback
            import uuid as _uuid
            fb = AIFeedback(
                id=_uuid.uuid4(),
                session_id=session_id,
                step_key=f"open_world_turn_{turn_index}",
                option_key=turn.intent.verb,
                feedback_text=feedback_text,
                key_insight=key_insight,
                coaching_question=coaching_question,
                consequence_analysis=consequence_analysis,
                alternative_path=alternative_path,
                prompt_version="v3.0-open-world",
                model_used="llama-3.3-70b-versatile",
                latency_ms=None,
                tone=tone,
                generated_at=datetime.now(timezone.utc),
            )
            db.add(fb)
            await db.flush()
            await db.refresh(fb)
            await db.commit()

            logger.info(
                "mentor_feedback_saved",
                session_id=str(session_id),
                turn_index=turn_index,
                tone=tone,
                feedback_id=str(fb.id),
            )
            return fb.id

        except Exception as e:
            logger.warning(
                "mentor_coach_failed",
                session_id=str(session_id),
                turn_index=turn_index,
                error=str(e),
            )
            return None
