from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import (
    LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse,
)
from app.api.schemas.common import ResponseEnvelope
from app.dependencies import CurrentUser, DBSession
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register", response_model=ResponseEnvelope[UserResponse], status_code=201)
async def register(body: RegisterRequest, db: DBSession):
    user = await auth_service.register(body.email, body.password, body.display_name, db)
    return ResponseEnvelope.ok(UserResponse.model_validate(user))


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(body: LoginRequest, db: DBSession):
    access, refresh = await auth_service.login(body.email, body.password, db)
    return ResponseEnvelope.ok(TokenResponse(access_token=access, refresh_token=refresh))


@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
async def refresh(body: RefreshRequest):
    access, refresh = await auth_service.refresh(body.refresh_token)
    return ResponseEnvelope.ok(TokenResponse(access_token=access, refresh_token=refresh))


@router.delete("/logout", status_code=204)
async def logout(current_user: CurrentUser):
    await auth_service.logout(current_user.id)


@router.get("/me", response_model=ResponseEnvelope[UserResponse])
async def get_me(current_user: CurrentUser):
    return ResponseEnvelope.ok(UserResponse.model_validate(current_user))
