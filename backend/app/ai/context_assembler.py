"""
ContextAssembler — builds a rich PromptContext from outcome + session history.

Improvements over v1:
- Full session arc (all decisions, not just step keys)
- Unchosen options included for alternative path analysis
- Metric trajectory from session start to now
- State flags forwarded for domain context
- RAG retrieval using BM25 on the step narrative + chosen option
"""
from app.ai.prompt_builder import DecisionHistoryItem, PromptContext
from app.ai.rag.retriever import Retriever
from app.config import settings
from app.simulation.models.outcome import StepOutcome
from app.simulation.models.session_state import SimSessionState

import structlog
logger = structlog.get_logger(__name__)


class ContextAssembler:

    def __init__(self, retriever: Retriever | None = None):
        # Retriever injected at construction — BM25 in production, None in tests
        self._retriever = retriever
        if settings.rag_enabled and retriever is None:
            try:
                from app.ai.rag.bm25_retriever import get_retriever
                self._retriever = get_retriever()
            except Exception as e:
                logger.warning("rag_init_failed", error=str(e))

    def build(
        self,
        outcome: StepOutcome,
        state: SimSessionState,
        profession_slug: str,
        db_history: list[dict] | None = None,
    ) -> PromptContext:
        """
        db_history: list of dicts from decision_log rows, ordered oldest → newest.
        Each dict should have: step_key, option_key, metrics_before, metrics_after,
        and optionally step_title, option_label.
        """
        session_history = self._build_history(db_history or [])

        # Build RAG query from the narrative + chosen option (richer signal than narrative alone)
        rag_docs: list[str] = []
        if self._retriever and self._retriever.is_ready():
            query_text = f"{outcome.step.narrative} {outcome.option.label}"
            try:
                rag_docs = self._retriever.query(
                    text=query_text,
                    filters={"profession": profession_slug},
                    top_k=3,
                )
            except Exception as e:
                logger.warning("rag_query_failed", error=str(e))

        # All options available at this step (for alternative analysis)
        all_options = [
            {
                "option_key": opt.option_key,
                "label": opt.label,
                "description": opt.description,
            }
            for opt in outcome.step.options
        ]

        return PromptContext(
            profession_slug=profession_slug,
            step_key=outcome.step.step_key,
            step_title=outcome.step.title,
            step_narrative=outcome.step.narrative,
            step_context_data=outcome.step.context_data,
            option_chosen_key=outcome.option.option_key,
            option_chosen_label=outcome.option.label,
            option_description=outcome.option.description,
            all_options=all_options,
            metrics_before=outcome.metrics_before.to_dict(),
            metrics_after=outcome.metrics_after.to_dict(),
            effects_applied=outcome.effects_applied,
            session_history=session_history,
            retrieved_context=rag_docs,
            state_flags=dict(state.state),
        )

    def _build_history(self, db_history: list[dict]) -> list[DecisionHistoryItem]:
        items = []
        for row in db_history[-settings.ai_feedback_history_depth:]:
            items.append(DecisionHistoryItem(
                step_key=row.get("step_key", ""),
                step_title=row.get("step_title", row.get("step_key", "")),
                option_key=row.get("option_key", ""),
                option_label=row.get("option_label", row.get("option_key", "")),
                metrics_before=row.get("metrics_before", {}),
                metrics_after=row.get("metrics_after", {}),
            ))
        return items
