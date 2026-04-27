from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.core.exceptions import ProfSimError, domain_exception_to_http
from app.core.logging import configure_logging
from app.db.session import close_db, init_db
from app.middleware.rate_limit import RateLimitMiddleware

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", env=settings.app_env)
    await init_db()

    from app.db.redis import init_redis, close_redis
    await init_redis()

    if settings.rag_enabled:
        try:
            from app.ai.rag.bm25_retriever import get_retriever
            get_retriever()
            logger.info("rag_warmed")
        except Exception as e:
            logger.warning("rag_warmup_failed", error=str(e))

        try:
            from app.ai.rag.tagged_retriever import get_tagged_retriever
            r = get_tagged_retriever()
            logger.info("tagged_rag_warmed", ready=r.is_ready())
        except Exception as e:
            logger.warning("tagged_rag_warmup_failed", error=str(e))

    try:
        from app.agents.image_library import get_library
        lib = get_library()
        logger.info("image_library_warmed", loaded=lib.has_loaded())
    except Exception as e:
        logger.warning("image_library_warmup_failed", error=str(e))

    try:
        from pathlib import Path
        from fastapi.staticfiles import StaticFiles
        images_dir = Path(__file__).parent / "agents" / "images"
        if images_dir.exists():
            app.mount("/static/images", StaticFiles(directory=str(images_dir)), name="images")
            logger.info("static_images_mounted", path=str(images_dir))
    except Exception as e:
        logger.warning("static_images_mount_failed", error=str(e))

    yield

    await close_db()
    from app.db.redis import close_redis
    await close_redis()
    logger.info("shutdown")


app = FastAPI(
    title="ProfSim API",
    description="AI-driven Interactive Profession Simulation Platform",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(ProfSimError)
async def profsim_exception_handler(request: Request, exc: ProfSimError):
    http_exc = domain_exception_to_http(exc)
    return ORJSONResponse(
        status_code=http_exc.status_code,
        content={
            "data": None,
            "meta": {
                "request_id": request.state.request_id
                if hasattr(request.state, "request_id") else None
            },
            "errors": http_exc.detail,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", exc_info=exc)
    return ORJSONResponse(
        status_code=500,
        content={
            "data": None,
            "meta": {},
            "errors": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
        },
    )


from app.api.v1 import router as v1_router  # noqa: E402
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "env": settings.app_env}
