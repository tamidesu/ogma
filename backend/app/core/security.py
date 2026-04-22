from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_access_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        if "expired" in str(e):
            raise TokenExpiredError()
        raise InvalidTokenError()

    if payload.get("type") != "access":
        raise InvalidTokenError()

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError()

    try:
        return UUID(sub)
    except ValueError:
        raise InvalidTokenError()


def decode_refresh_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        if "expired" in str(e):
            raise TokenExpiredError()
        raise InvalidTokenError()

    if payload.get("type") != "refresh":
        raise InvalidTokenError()

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError()

    try:
        return UUID(sub)
    except ValueError:
        raise InvalidTokenError()
