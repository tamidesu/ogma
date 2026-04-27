"""
Repositories for the open-world simulation flow.

  OpenWorldRepo — wraps all DB operations for one turn:
    • read / write NPCState
    • write AgentTurn
    • write WorldStateSnapshot
    • read turn count (for turn_index)
    • read world state from latest snapshot

Kept intentionally thin: just SQLAlchemy + datetime glue.
All business logic stays in the orchestrator.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class OpenWorldRepo:

    # ── NPC state ─────────────────────────────────────────────────────

    async def get_npc_state(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> dict | None:
        from app.db.models.npc_state import NPCState
        result = await db.execute(
            select(NPCState).where(NPCState.session_id == session_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {
            "definition_id": row.definition_id,
            "emotion": row.emotion_json,
            "relationship_score": row.relationship_score,
            "memory": row.memory_json or [],
            "current_label": row.current_label,
            "current_avatar_id": row.current_avatar_id,
        }

    async def upsert_npc_state(
        self,
        session_id: uuid.UUID,
        definition_id: str,
        emotion: dict,
        relationship_score: int,
        memory: list,
        current_label: str | None,
        current_avatar_id: str | None,
        db: AsyncSession,
    ) -> None:
        from app.db.models.npc_state import NPCState
        now = datetime.now(timezone.utc)
        stmt = pg_insert(NPCState).values(
            session_id=session_id,
            definition_id=definition_id,
            emotion_json=emotion,
            relationship_score=relationship_score,
            memory_json=memory,
            current_label=current_label,
            current_avatar_id=current_avatar_id,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=[NPCState.session_id],
            set_={
                "emotion_json": emotion,
                "relationship_score": relationship_score,
                "memory_json": memory,
                "current_label": current_label,
                "current_avatar_id": current_avatar_id,
                "updated_at": now,
            },
        )
        await db.execute(stmt)

    # ── Turn count ────────────────────────────────────────────────────

    async def next_turn_index(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> int:
        from app.db.models.agent_turn import AgentTurn
        result = await db.execute(
            select(func.count()).where(AgentTurn.session_id == session_id)
        )
        count = result.scalar_one() or 0
        return int(count)

    # ── World state ───────────────────────────────────────────────────

    async def get_latest_world_state(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> dict | None:
        from app.db.models.world_state_snapshot import WorldStateSnapshot
        result = await db.execute(
            select(WorldStateSnapshot)
            .where(WorldStateSnapshot.session_id == session_id)
            .order_by(WorldStateSnapshot.turn_index.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row.state_json if row else None

    async def write_world_snapshot(
        self,
        session_id: uuid.UUID,
        turn_index: int,
        state: dict,
        db: AsyncSession,
    ) -> None:
        from app.db.models.world_state_snapshot import WorldStateSnapshot
        snap = WorldStateSnapshot(
            id=uuid.uuid4(),
            session_id=session_id,
            turn_index=turn_index,
            state_json=state,
            created_at=datetime.now(timezone.utc),
        )
        db.add(snap)

    # ── Agent turn ────────────────────────────────────────────────────

    async def write_agent_turn(
        self,
        session_id: uuid.UUID,
        turn_index: int,
        user_input: str,
        locale: str,
        intent_json: dict,
        validation_json: dict,
        npc_update_json: dict,
        world_delta_json: dict,
        image_id: str | None,
        is_terminal: bool,
        termination_reason: str | None,
        pipeline_latency_ms: int | None,
        db: AsyncSession,
    ) -> uuid.UUID:
        from app.db.models.agent_turn import AgentTurn
        turn = AgentTurn(
            id=uuid.uuid4(),
            session_id=session_id,
            turn_index=turn_index,
            user_input=user_input,
            locale=locale,
            intent_json=intent_json,
            validation_json=validation_json,
            npc_update_json=npc_update_json,
            world_delta_json=world_delta_json,
            image_id=image_id,
            is_terminal=is_terminal,
            termination_reason=termination_reason,
            pipeline_latency_ms=pipeline_latency_ms,
            created_at=datetime.now(timezone.utc),
        )
        db.add(turn)
        await db.flush()
        return turn.id

    async def set_mentor_feedback_id(
        self,
        turn_id: uuid.UUID,
        feedback_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        from app.db.models.agent_turn import AgentTurn
        result = await db.execute(
            select(AgentTurn).where(AgentTurn.id == turn_id)
        )
        turn = result.scalar_one_or_none()
        if turn:
            turn.mentor_feedback_id = feedback_id

    # ── Session brief lookup ──────────────────────────────────────────

    async def get_session_brief_id(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> uuid.UUID | None:
        from app.db.models.sim_session import SimulationSession
        result = await db.execute(
            select(SimulationSession.brief_id)
            .where(SimulationSession.id == session_id)
        )
        return result.scalar_one_or_none()
