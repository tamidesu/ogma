"""
DomainValidator — RAG-grounded judgment on the user's intended action.

Retrieves relevant knowledge chunks via TaggedMarkdownRetriever, then makes
a single Groq JSON-mode call to judge legality, SoC, severity, and citations.
Only sets blocks_action=True for 'critical' severity.
"""
from __future__ import annotations

from pathlib import Path

import structlog

from app.agents.groq_helper import call_groq_json
from app.agents.schemas import Citation, Intent, ScenarioBriefData, ValidationResult

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "validator.system.md"

_SAFE_VALIDATION = ValidationResult(
    is_legal=True,
    is_standard_of_care=True,
    severity_if_wrong="minor",
    citations=[],
    coach_note="Жүйе дәрігерді тексере алмады — жалғастырыңыз.",
    blocks_action=False,
)

_SEVERITIES = {"minor", "moderate", "severe", "critical"}


def _build_user_prompt(
    intent: Intent,
    brief: ScenarioBriefData,
    world_state: dict,
    retrieved_chunks: list,
) -> str:
    lines = [
        "## Brief context",
        f"Profession: {brief.profession_slug}",
        f"NPC: {brief.npc_definition.display_name} ({brief.npc_definition.role})",
        "",
        "## Current world state (abbreviated)",
        f"Metrics: {world_state.get('metrics', {})}",
        f"Flags: {world_state.get('flags', {})}",
        f"Phase: {(world_state.get('time') or {}).get('current_phase', 'unknown')}",
        "",
        "## User's intended action (structured)",
        f"verb: {intent.verb}",
        f"target: {intent.target}",
        f"parameters: {intent.parameters}",
        f"paraphrase: {intent.raw_paraphrase}",
        "",
        "## Retrieved knowledge chunks",
    ]
    if retrieved_chunks:
        for i, chunk in enumerate(retrieved_chunks, 1):
            lines += [
                f"### Chunk {i} — [{chunk.citation}] (tag: {chunk.tag}, score: {chunk.score:.2f})",
                chunk.text[:600],
            ]
    else:
        lines.append("(No relevant chunks retrieved — judge based on general medical knowledge.)")
    return "\n".join(lines)


def _parse_validation(data: dict) -> ValidationResult:
    severity = str(data.get("severity_if_wrong", "minor")).lower()
    if severity not in _SEVERITIES:
        severity = "minor"

    raw_citations = data.get("citations") or []
    citations = []
    for c in raw_citations[:3]:
        if not isinstance(c, dict):
            continue
        citations.append(Citation(
            source=str(c.get("source", "")),
            snippet=str(c.get("snippet", "")),
            tag=str(c.get("tag", "")),
            relevance=float(c.get("relevance", 0.0)),
        ))

    blocks = bool(data.get("blocks_action", False)) and severity == "critical"

    return ValidationResult(
        is_legal=bool(data.get("is_legal", True)),
        is_standard_of_care=bool(data.get("is_standard_of_care", True)),
        severity_if_wrong=severity,  # type: ignore[arg-type]
        citations=citations,
        coach_note=str(data.get("coach_note", "")),
        blocks_action=blocks,
    )


class DomainValidator:

    async def validate(
        self,
        intent: Intent,
        brief: ScenarioBriefData,
        world_state: dict,
    ) -> ValidationResult:
        # ── RAG retrieval ─────────────────────────────────────────────
        from app.ai.rag.tagged_retriever import get_tagged_retriever
        retriever = get_tagged_retriever()
        query = f"{intent.verb} {intent.target} {intent.raw_paraphrase}"
        chunks = retriever.query(
            text=query,
            profession=brief.profession_slug,
            knowledge_tags=brief.knowledge_tags or None,
            top_k=3,
        )

        system = _PROMPT_PATH.read_text(encoding="utf-8")
        user = _build_user_prompt(intent, brief, world_state, chunks)

        try:
            data = await call_groq_json(
                system_prompt=system,
                user_prompt=user,
                max_tokens=420,
                temperature=0.2,
                schema_hint="ValidationResult",
            )
            result = _parse_validation(data)
            logger.info(
                "validation_done",
                soc=result.is_standard_of_care,
                severity=result.severity_if_wrong,
                blocks=result.blocks_action,
                citations=len(result.citations),
            )
            return result
        except Exception as e:
            logger.warning("validator_fallback", error=str(e))
            return _SAFE_VALIDATION
