from fastapi import APIRouter

from app.api.v1 import auth, professions, sessions, progress, briefs, open_world

router = APIRouter()
router.include_router(auth.router)
router.include_router(professions.router)
router.include_router(sessions.router)
router.include_router(progress.router)
router.include_router(briefs.router)
router.include_router(open_world.router)
