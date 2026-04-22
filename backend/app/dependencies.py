from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, InvalidTokenError, TokenExpiredError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.db.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

DBSession = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UUID:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Authorization header required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_access_token(credentials.credentials)
    except (TokenExpiredError, InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    session: DBSession,
) -> User:
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User not found or inactive"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserID = Annotated[UUID, Depends(get_current_user_id)]
