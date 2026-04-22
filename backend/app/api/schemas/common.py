from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    data: T | None = None
    meta: dict[str, Any] = {}
    errors: Any = None

    @classmethod
    def ok(cls, data: T, **meta) -> "ResponseEnvelope[T]":
        return cls(data=data, meta=meta)

    @classmethod
    def error(cls, code: str, message: str) -> "ResponseEnvelope":
        return cls(data=None, errors={"code": code, "message": message})


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool
