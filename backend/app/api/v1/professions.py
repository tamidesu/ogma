from uuid import UUID

from fastapi import APIRouter

from app.api.schemas.common import ResponseEnvelope
from app.api.schemas.simulation import ProfessionResponse, ScenarioSummaryResponse
from app.core.exceptions import NotFoundError
from app.dependencies import CurrentUser, DBSession
from app.db.repositories.scenario_repo import ScenarioRepository

router = APIRouter(prefix="/professions", tags=["professions"])
scenario_repo = ScenarioRepository()


@router.get("", response_model=ResponseEnvelope[list[ProfessionResponse]])
async def list_professions(db: DBSession, _: CurrentUser):
    professions = await scenario_repo.list_professions(db)
    return ResponseEnvelope.ok([ProfessionResponse.model_validate(p) for p in professions])


@router.get("/{profession_id}/scenarios", response_model=ResponseEnvelope[list[ScenarioSummaryResponse]])
async def list_scenarios(profession_id: UUID, db: DBSession, _: CurrentUser):
    scenarios = await scenario_repo.list_scenarios(profession_id, db)
    return ResponseEnvelope.ok([ScenarioSummaryResponse.model_validate(s) for s in scenarios])


@router.get("/{profession_id}", response_model=ResponseEnvelope[ProfessionResponse])
async def get_profession(profession_id: UUID, db: DBSession, _: CurrentUser):
    from sqlalchemy import select
    from app.db.models.profession import Profession
    result = await db.execute(
        select(Profession).where(Profession.id == profession_id, Profession.is_active == True)
    )
    profession = result.scalar_one_or_none()
    if not profession:
        raise NotFoundError("Profession", str(profession_id))
    return ResponseEnvelope.ok(ProfessionResponse.model_validate(profession))
