import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_refresh_token,
)
from app.db.models.user import User
from app.db.repositories.user_repo import UserRepository
from app.db.redis import get_redis

logger = structlog.get_logger(__name__)
user_repo = UserRepository()


class AuthService:

    async def register(
        self,
        email: str,
        password: str,
        display_name: str | None,
        db: AsyncSession,
    ) -> User:
        existing = await user_repo.get_by_email(email, db)
        if existing:
            raise ConflictError(f"Email already registered: {email}")

        hashed = hash_password(password)
        user = await user_repo.create(email, hashed, display_name, db)
        logger.info("user_registered", user_id=str(user.id), email=email)
        return user

    async def login(
        self, email: str, password: str, db: AsyncSession
    ) -> tuple[str, str]:
        """Returns (access_token, refresh_token)."""
        user = await user_repo.get_by_email(email, db)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        # Store refresh token in Redis
        redis = await get_redis()
        from app.config import settings
        await redis.setex(
            f"refresh:{str(user.id)}",
            settings.redis_refresh_token_ttl,
            refresh_token,
        )

        logger.info("user_login", user_id=str(user.id))
        return access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Rotate refresh token — returns new (access, refresh) pair."""
        user_id = decode_refresh_token(refresh_token)

        redis = await get_redis()
        stored = await redis.get(f"refresh:{str(user_id)}")
        if stored != refresh_token:
            raise AuthenticationError("Refresh token is invalid or expired")

        new_access = create_access_token(user_id)
        new_refresh = create_refresh_token(user_id)

        from app.config import settings
        await redis.setex(
            f"refresh:{str(user_id)}",
            settings.redis_refresh_token_ttl,
            new_refresh,
        )
        return new_access, new_refresh

    async def logout(self, user_id) -> None:
        redis = await get_redis()
        await redis.delete(f"refresh:{str(user_id)}")
        logger.info("user_logout", user_id=str(user_id))
