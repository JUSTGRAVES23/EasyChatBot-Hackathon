from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
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


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    detail: str


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(
        min_length=1,
        max_length=512,
    )
    new_password: str = Field(
        min_length=12,
        max_length=256,
    )


class PasswordResetConfirmResponse(BaseModel):
    detail: str


class PasswordResetContextResponse(BaseModel):
    email: EmailStr


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


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password reset",
    description=(
        "Request a password reset email. The outward response does not "
        "reveal whether the supplied email belongs to an account."
    ),
)
async def request_password_reset(
    request: PasswordResetRequest,
    http_request: Request,
) -> PasswordResetRequestResponse:
    """
    Request a password-reset email.

    The route delegates entirely to the composed authentication service.
    Account lookup, reset-token creation, rate limiting and email delivery
    remain application/repository/provider responsibilities.

    The response deliberately uses generic wording so that account existence
    is not disclosed to the caller.
    """
    service = http_request.app.state.authentication_service

    try:
        await service.request_password_reset(
            email=str(request.email),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    return PasswordResetRequestResponse(
        detail=(
            "If an account exists for that email address, "
            "a password reset email has been sent."
        ),
    )


@router.get(
    "/password-reset/context",
    response_model=PasswordResetContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve password-reset account context",
    description=(
        "Return the account email associated with a valid, unused, "
        "unexpired password-reset token. No token, password, credential "
        "hash, username, or session data is returned."
    ),
)
async def get_password_reset_context(
    http_request: Request,
    response: Response,
    token: str = Query(
        min_length=1,
        max_length=512,
    ),
) -> PasswordResetContextResponse:
    """Resolve a reset token to the account email for the reset UI."""
    response.headers["Cache-Control"] = "no-store"
    service = http_request.app.state.authentication_service

    try:
        context = await service.get_password_reset_context(
            token=token,
        )
    except AuthenticationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
            headers={"Cache-Control": "no-store"},
        )

    return PasswordResetContextResponse(email=context.email)


@router.post(
    "/password-reset/confirm",
    response_model=PasswordResetConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a password reset",
    description=(
        "Replace the account password using a valid, single-use password "
        "reset token."
    ),
)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    http_request: Request,
) -> PasswordResetConfirmResponse:
    """
    Complete a password reset.

    The raw reset token is accepted only as transient request data and is
    delegated to the application service. The route never logs, persists,
    or returns the token.
    """
    service = http_request.app.state.authentication_service

    try:
        await service.confirm_password_reset(
            token=request.token,
            new_password=request.new_password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    return PasswordResetConfirmResponse(
        detail=(
            "Password reset successful. "
            "You can now sign in with your new password."
        ),
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
    "PasswordResetRequest",
    "PasswordResetRequestResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetConfirmResponse",
    "PasswordResetContextResponse",
]
