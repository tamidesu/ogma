from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context_assembler import ContextAssembler
from app.ai.groq_adapter import GroqAdapter
from app.ai.prompt_builder import PromptBuilder
from app.ai.provider_adapter import AIProvider, FeedbackResult
from app.db.models.ai_feedback import AIFeedback
from app.simulation.models.outcome import StepOutcome
from app.simulation.models.session_state import SimSessionState

logger = structlog.get_logger(__name__)


class FeedbackGenerator:

    def __init__(self, provider: AIProvider | None = None):
        self._provider = provider or GroqAdapter()
        self._builder = PromptBuilder()
        self._assembler = ContextAssembler()

    async def generate(
        self,
        outcome: StepOutcome,
        state: SimSessionState,
        profession_slug: str,
        session_id: UUID,
        db: AsyncSession,
        db_history: list[dict] | None = None,
    ) -> AIFeedback | None:
        """
        Generate structured AI feedback and persist it.
        Called as a BackgroundTask — exceptions are swallowed and logged.
        db_history: list of dicts with keys: step_key, step_title, option_key,
                    option_label, metrics_before, metrics_after
        """
        try:
            ctx = self._assembler.build(outcome, state, profession_slug, db_history)
            system_prompt = self._builder.build_system_prompt(profession_slug)
            user_prompt = self._builder.build_user_prompt(ctx)

            result: FeedbackResult = await self._provider.generate_feedback(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=700,
            )

            feedback = AIFeedback(
                session_id=session_id,
                step_key=outcome.step.step_key,
                option_key=outcome.option.option_key,
                feedback_text=result.text,
                key_insight=result.key_insight,
                coaching_question=result.coaching_question,
                consequence_analysis=result.consequence_analysis,
                alternative_path=result.structured.alternative_path,
                prompt_version=result.prompt_version,
                model_used=result.model,
                latency_ms=result.latency_ms,
                tone=result.tone,
                generated_at=datetime.now(timezone.utc),
            )
            db.add(feedback)
            await db.flush()
            await db.refresh(feedback)
            await db.commit()

            logger.info(
                "feedback_generated",
                session_id=str(session_id),
                step_key=outcome.step.step_key,
                latency_ms=result.latency_ms,
                tone=result.tone,
            )
            return feedback

        except Exception as e:
            logger.error(
                "feedback_generation_failed",
                session_id=str(session_id),
                error=str(e),
                exc_info=True,
            )
            return None
