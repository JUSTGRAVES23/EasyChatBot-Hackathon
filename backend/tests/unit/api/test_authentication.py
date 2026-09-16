from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from app.api.authentication import (
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    confirm_password_reset,
    get_password_reset_context,
    get_session,
    login,
    logout,
    register,
    request_password_reset,
    verify_email,
)
from app.domain.identity.principal import Principal


def build_request(
    service: AsyncMock,
    *,
    headers: dict[str, str] | None = None,
    client_host: str = "127.0.0.1",
    cookies: str | None = None,
) -> Request:
    app = SimpleNamespace(
        state=SimpleNamespace(authentication_service=service)
    )

    scope = {
        "type": "http",
        "app": app,
        "method": "POST",
        "path": "/auth/test",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in (headers or {}).items()
        ],
        "client": (client_host, 12345),
        "scheme": "https",
        "server": ("testserver", 443),
        "query_string": b"",
        "root_path": "",
        "http_version": "1.1",
    }

    if cookies is not None:
        scope["headers"].append((b"cookie", cookies.encode()))

    return Request(scope)


def build_principal(*, is_active: bool = True) -> Principal:
    # The route only consumes the public `is_active` contract.
    return SimpleNamespace(is_active=is_active)  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_register_delegates_to_composed_authentication_service() -> None:
    service = AsyncMock()
    user_id = uuid4()
    service.register.return_value = user_id

    request = RegisterRequest(
        email="USER@example.com",
        username="testuser",
        password="Strong-password-123!",
    )
    http_request = build_request(service)

    result = await register(request, http_request)

    assert result.user_id == user_id
    assert result.detail == (
        "Registration successful. Email verification is required."
    )
    service.register.assert_awaited_once_with(
        email="USER@example.com",
        username="testuser",
        password="Strong-password-123!",
    )


@pytest.mark.asyncio
async def test_register_maps_authentication_error_to_bad_request() -> None:
    service = AsyncMock()
    from app.application.identity.authentication_service import AuthenticationError

    service.register.side_effect = AuthenticationError("Registration failed")
    http_request = build_request(service)

    with pytest.raises(HTTPException) as exc_info:
        await register(
            RegisterRequest(
                email="user@example.com",
                username="testuser",
                password="Strong-password-123!",
            ),
            http_request,
        )

    assert getattr(exc_info.value, "status_code", None) == 400
    assert getattr(exc_info.value, "detail", None) == "Registration failed"


@pytest.mark.asyncio
async def test_login_creates_secure_session_cookie_and_returns_expiry() -> None:
    service = AsyncMock()
    session_id = uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    service.authenticate.return_value = SimpleNamespace(
        session_id=session_id,
        expires_at=expires_at,
    )

    http_request = build_request(
        service,
        headers={"user-agent": "EasyChatBot-Test/1.0"},
        client_host="192.0.2.10",
    )
    response = Response()

    result = await login(
        LoginRequest(
            email=" USER@example.com ",
            password="Strong-password-123!",
        ),
        http_request,
        response,
    )

    assert result.detail == "Login successful."
    assert result.expires_at == expires_at.isoformat()

    service.authenticate.assert_awaited_once_with(
        email="USER@example.com",
        password="Strong-password-123!",
        device_name="EasyChatBot-Test/1.0",
        ip_address="192.0.2.10",
    )

    cookie = response.headers["set-cookie"]
    assert f"easychatbot_session={session_id}" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie


@pytest.mark.asyncio
async def test_login_maps_authentication_error_to_unauthorized() -> None:
    from app.application.identity.authentication_service import AuthenticationError

    service = AsyncMock()
    service.authenticate.side_effect = AuthenticationError("Invalid credentials")

    http_request = build_request(service)
    response = Response()

    with pytest.raises(HTTPException) as exc_info:
        await login(
            LoginRequest(
                email="user@example.com",
                password="Strong-password-123!",
            ),
            http_request,
            response,
        )

    assert getattr(exc_info.value, "status_code", None) == 401
    assert getattr(exc_info.value, "detail", None) == "Invalid credentials"
    assert getattr(exc_info.value, "headers", {}).get("WWW-Authenticate") == "Session"


@pytest.mark.asyncio
async def test_session_exposes_only_authentication_state() -> None:
    result = await get_session(build_principal(is_active=True))

    assert result.authenticated is True
    assert not hasattr(result, "session_id")


@pytest.mark.asyncio
async def test_password_reset_request_delegates_and_returns_generic_response() -> None:
    service = AsyncMock()
    http_request = build_request(service)

    result = await request_password_reset(
        PasswordResetRequest(email="USER@example.com"),
        http_request,
    )

    assert result.detail == (
        "If an account exists for that email address, "
        "a password reset email has been sent."
    )
    service.request_password_reset.assert_awaited_once_with(
        email="USER@example.com",
    )


@pytest.mark.asyncio
async def test_password_reset_request_maps_service_error_to_bad_request() -> None:
    from app.application.identity.authentication_service import AuthenticationError

    service = AsyncMock()
    service.request_password_reset.side_effect = AuthenticationError(
        "Password reset failed"
    )
    http_request = build_request(service)

    with pytest.raises(HTTPException) as exc_info:
        await request_password_reset(
            PasswordResetRequest(email="user@example.com"),
            http_request,
        )

    assert getattr(exc_info.value, "status_code", None) == 400
    assert getattr(exc_info.value, "detail", None) == "Password reset failed"


@pytest.mark.asyncio
async def test_password_reset_context_returns_email_and_no_store_cache_header() -> None:
    service = AsyncMock()
    service.get_password_reset_context.return_value = SimpleNamespace(
        email="user@example.com"
    )
    http_request = build_request(service)
    response = Response()

    result = await get_password_reset_context(
        http_request,
        response,
        token="valid-reset-token",
    )

    assert result.email == "user@example.com"
    assert response.headers["cache-control"] == "no-store"
    service.get_password_reset_context.assert_awaited_once_with(
        token="valid-reset-token",
    )


@pytest.mark.asyncio
async def test_password_reset_context_maps_error_to_no_store_bad_request() -> None:
    from app.application.identity.authentication_service import AuthenticationError

    service = AsyncMock()
    service.get_password_reset_context.side_effect = AuthenticationError(
        "Invalid or expired password reset token"
    )
    http_request = build_request(service)
    response = Response()

    result = await get_password_reset_context(
        http_request,
        response,
        token="invalid-token",
    )

    # JSONResponse is returned directly by the route for this failure path.
    assert result.status_code == 400
    assert result.headers["cache-control"] == "no-store"
    assert result.body == (
        b'{"detail":"Invalid or expired password reset token"}'
    )


@pytest.mark.asyncio
async def test_confirm_password_reset_delegates_raw_token_and_new_password() -> None:
    service = AsyncMock()
    http_request = build_request(service)

    result = await confirm_password_reset(
        PasswordResetConfirmRequest(
            token=" reset-token-123 ",
            new_password="New-Strong-Password-123!",
        ),
        http_request,
    )

    assert result.detail == (
        "Password reset successful. "
        "You can now sign in with your new password."
    )
    service.confirm_password_reset.assert_awaited_once_with(
        token=" reset-token-123 ",
        new_password="New-Strong-Password-123!",
    )


@pytest.mark.asyncio
async def test_confirm_password_reset_maps_service_error_to_bad_request() -> None:
    from app.application.identity.authentication_service import AuthenticationError

    service = AsyncMock()
    service.confirm_password_reset.side_effect = AuthenticationError(
        "Invalid or expired password reset token"
    )
    http_request = build_request(service)

    with pytest.raises(HTTPException) as exc_info:
        await confirm_password_reset(
            PasswordResetConfirmRequest(
                token="invalid-token",
                new_password="New-Strong-Password-123!",
            ),
            http_request,
        )

    assert getattr(exc_info.value, "status_code", None) == 400
    assert (
        getattr(exc_info.value, "detail", None)
        == "Invalid or expired password reset token"
    )


@pytest.mark.asyncio
async def test_verify_email_delegates_token_and_returns_success() -> None:
    service = AsyncMock()
    http_request = build_request(service)

    result = await verify_email(
        token="verification-token-123",
        http_request=http_request,
    )

    assert result == {"detail": "Email verification successful."}
    service.verify_email.assert_awaited_once_with("verification-token-123")


@pytest.mark.asyncio
async def test_verify_email_maps_service_error_to_bad_request() -> None:
    from app.application.identity.authentication_service import AuthenticationError

    service = AsyncMock()
    service.verify_email.side_effect = AuthenticationError(
        "Invalid or expired verification token"
    )
    http_request = build_request(service)

    with pytest.raises(HTTPException) as exc_info:
        await verify_email(
            token="invalid-token",
            http_request=http_request,
        )

    assert getattr(exc_info.value, "status_code", None) == 400
    assert (
        getattr(exc_info.value, "detail", None)
        == "Invalid or expired verification token"
    )


@pytest.mark.asyncio
async def test_logout_revokes_valid_session_and_deletes_cookie() -> None:
    service = AsyncMock()
    session_id = uuid4()
    http_request = build_request(
        service,
        cookies=f"easychatbot_session={session_id}",
    )
    response = Response()

    result = await logout(http_request, response)

    assert result is None
    service.revoke_session.assert_awaited_once_with(session_id)

    cookie = response.headers["set-cookie"]
    assert "easychatbot_session=" in cookie
    assert "Max-Age=0" in cookie
    assert "Path=/" in cookie


@pytest.mark.asyncio
async def test_logout_does_not_call_service_for_invalid_session_cookie() -> None:
    service = AsyncMock()
    http_request = build_request(
        service,
        cookies="easychatbot_session=not-a-uuid",
    )
    response = Response()

    await logout(http_request, response)

    service.revoke_session.assert_not_awaited()
    assert "easychatbot_session=" in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_logout_without_cookie_only_deletes_cookie() -> None:
    service = AsyncMock()
    http_request = build_request(service)
    response = Response()

    await logout(http_request, response)

    service.revoke_session.assert_not_awaited()
    assert "easychatbot_session=" in response.headers["set-cookie"]


def test_request_models_enforce_password_and_token_boundaries() -> None:
    with pytest.raises(ValueError):
        RegisterRequest(
            email="user@example.com",
            username="u",
            password="short",
        )

    with pytest.raises(ValueError):
        PasswordResetConfirmRequest(
            token="",
            new_password="New-Strong-Password-123!",
        )

    with pytest.raises(ValueError):
        PasswordResetConfirmRequest(
            token="valid-token",
            new_password="short",
        )


def test_password_reset_request_requires_valid_email() -> None:
    with pytest.raises(ValueError):
        PasswordResetRequest(email="not-an-email")
