from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

logger = structlog.get_logger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.is_development,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    from app.db.base import Base  # noqa: F401 — import all models to register them
    import app.db.models  # noqa: F401

    async with engine.begin() as conn:
        logger.info("db_connected", url=settings.database_url.split("@")[-1])


async def close_db() -> None:
    await engine.dispose()
    logger.info("db_disconnected")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Alias for use in background tasks that need their own session
AsyncSessionLocal = async_session_factory
