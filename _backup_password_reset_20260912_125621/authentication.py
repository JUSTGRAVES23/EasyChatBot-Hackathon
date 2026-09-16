from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.api.dependencies.identity import get_current_principal
from app.application.identity.authentication_service import AuthenticationError
from app.domain.identity.principal import Principal


# NOTE:
# The authentication service must be composed into app.state
# by the application's existing bootstrap/composition root.
#
# Routes intentionally consume the composed application service rather than
# constructing AuthenticationService instances themselves. This preserves
# the production dependency graph, including authentication email delivery.


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=2,
        max_length=100,
    )
    password: str = Field(
        min_length=12,
        max_length=256,
    )


class RegisterResponse(BaseModel):
    user_id: UUID
    detail: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=256,
    )


class LoginResponse(BaseModel):
    detail: str
    expires_at: str


class SessionResponse(BaseModel):
    authenticated: bool


@router.get(
    "/session",
    response_model=SessionResponse,
    summary="Check the current authentication session",
    description=(
        "Return whether the current request has a valid authenticated "
        "application session. The session identifier and other sensitive "
        "authentication data are never returned."
    ),
)
async def get_session(
    principal: Principal = Depends(get_current_principal),
) -> SessionResponse:
    """
    Return the current authentication state.

    Authentication is resolved exclusively through the existing
    get_current_principal() dependency and SessionIdentityProvider.

    This endpoint intentionally exposes only authentication state.
    It does not expose the session identifier, credentials, or other
    sensitive authentication material.
    """
    return SessionResponse(
        authenticated=principal.is_active,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    http_request: Request,
) -> RegisterResponse:
    """
    Register a new account through the composed authentication service.

    Registration creates the account and verification token and triggers
    verification-email delivery through the configured application/provider
    boundary. The route itself does not select or call an email provider.
    """
    service = http_request.app.state.authentication_service

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
        detail=(
            "Registration successful. "
            "Email verification is required."
        ),
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
    """
    Authenticate through the composed authentication service.

    The service enforces account status and email verification before a
    server-side session is created.
    """
    service = http_request.app.state.authentication_service

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
            headers={
                "WWW-Authenticate": "Session",
            },
        ) from None

    expires_in_seconds = max(
        0,
        int(
            (
                result.expires_at
                - datetime.now(timezone.utc)
            ).total_seconds()
        ),
    )

    response.set_cookie(
        key="easychatbot_session",
        value=str(result.session_id),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=expires_in_seconds,
        path="/",
    )

    return LoginResponse(
        detail="Login successful.",
        expires_at=result.expires_at.isoformat(),
    )


@router.post("/verify-email")
async def verify_email(
    token: str,
    http_request: Request,
) -> dict[str, str]:
    """Verify an application email address.

    Token validation, expiration and single-use enforcement remain inside
    the authentication repository.
    """
    service = http_request.app.state.authentication_service

    try:
        await service.verify_email(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    return {
        "detail": "Email verification successful.",
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    http_request: Request,
    response: Response,
) -> None:
    """
    Revoke the current server-side authentication session.

    No authentication service is constructed here; the application's
    composed authentication service is reused.
    """
    session_id = http_request.cookies.get(
        "easychatbot_session"
    )

    if session_id:
        service = http_request.app.state.authentication_service

        try:
            parsed_session_id = UUID(session_id)
        except ValueError:
            parsed_session_id = None

        if parsed_session_id is not None:
            await service.revoke_session(
                parsed_session_id
            )

    response.delete_cookie(
        key="easychatbot_session",
        path="/",
    )


__all__ = [
    "router",
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    "SessionResponse",
]