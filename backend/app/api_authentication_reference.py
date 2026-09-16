from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.application.identity.authentication_service import (
    AuthenticationError,
    AuthenticationService,
)

# NOTE:
# The authentication service/repository must be composed into app.state
# by the application's existing bootstrap/composition root.


router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=256)


class RegisterResponse(BaseModel):
    user_id: UUID
    detail: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    detail: str
    expires_at: str


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    http_request: Request,
) -> RegisterResponse:
    service = AuthenticationService(
        http_request.app.state.auth_repository
    )

    try:
        user_id = await service.register(
            email=str(request.email),
            username=request.username,
            password=request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    return RegisterResponse(
        user_id=user_id,
        detail="Registration successful. Email verification is required.",
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
) -> LoginResponse:
    service = AuthenticationService(
        http_request.app.state.auth_repository
    )

    try:
        result = await service.authenticate(
            email=str(request.email),
            password=request.password,
            device_name=http_request.headers.get("user-agent"),
            ip_address=(
                http_request.client.host
                if http_request.client
                else None
            ),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Session"},
        ) from None

    response.set_cookie(
        key="easychatbot_session",
        value=str(result.session_id),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(
            (result.expires_at - __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            )).total_seconds()
        ),
        path="/",
    )

    return LoginResponse(
        detail="Login successful.",
        expires_at=result.expires_at.isoformat(),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    http_request: Request,
    response: Response,
) -> None:
    session_id = http_request.cookies.get("easychatbot_session")

    if session_id:
        service = AuthenticationService(
            http_request.app.state.auth_repository
        )
        await service.revoke_session(UUID(session_id))

    response.delete_cookie(
        key="easychatbot_session",
        path="/",
    )

