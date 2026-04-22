from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:

    async def get_by_id(self, user_id: UUID, session: AsyncSession) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, session: AsyncSession) -> User | None:
        result = await session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(
        self, email: str, hashed_password: str, display_name: str | None, session: AsyncSession
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            display_name=display_name,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def update_display_name(
        self, user: User, display_name: str, session: AsyncSession
    ) -> User:
        user.display_name = display_name
        await session.flush()
        return user
