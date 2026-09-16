from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.authentication import router as authentication_router
from app.application.identity.authentication_service import AuthenticationError


pytestmark = pytest.mark.integration


def _create_app(
    authentication_service: AsyncMock,
) -> FastAPI:
    app = FastAPI()
    app.state.authentication_service = authentication_service
    app.include_router(authentication_router)
    return app


@pytest.mark.asyncio
async def test_password_reset_request_returns_generic_accepted_response() -> None:
    service = AsyncMock()

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "user@example.com"},
        )

    assert response.status_code == 202

    assert response.json() == {
        "detail": (
            "If an account exists for that email address, "
            "a password reset email has been sent."
        )
    }

    service.request_password_reset.assert_awaited_once_with(
        email="user@example.com",
    )


@pytest.mark.asyncio
async def test_password_reset_request_does_not_disclose_unknown_email() -> None:
    service = AsyncMock()

    service.request_password_reset.return_value = None

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "unknown@example.com"},
        )

    assert response.status_code == 202

    assert "unknown@example.com" not in response.text
    assert "does not exist" not in response.text.lower()
    assert "not found" not in response.text.lower()


@pytest.mark.asyncio
async def test_password_reset_request_maps_authentication_error_to_bad_request() -> None:
    service = AsyncMock()

    service.request_password_reset.side_effect = AuthenticationError(
        "A valid email is required."
    )

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "invalid@example.com"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "A valid email is required."


@pytest.mark.asyncio
async def test_password_reset_request_rejects_invalid_email_schema() -> None:
    service = AsyncMock()

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "not-an-email"},
        )

    assert response.status_code == 422
    service.request_password_reset.assert_not_awaited()


@pytest.mark.asyncio
async def test_password_reset_confirm_returns_success_without_exposing_token() -> None:
    service = AsyncMock()

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "raw-reset-token",
                "new_password": "New-Secure-Password-2026!",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "detail": (
            "Password reset successful. "
            "You can now sign in with your new password."
        )
    }

    assert "raw-reset-token" not in response.text

    service.confirm_password_reset.assert_awaited_once_with(
        token="raw-reset-token",
        new_password="New-Secure-Password-2026!",
    )


@pytest.mark.asyncio
async def test_password_reset_confirm_maps_invalid_token_to_bad_request() -> None:
    service = AsyncMock()

    service.confirm_password_reset.side_effect = AuthenticationError(
        "Invalid or expired password reset token."
    )

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "expired-token",
                "new_password": "New-Secure-Password-2026!",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset token."
    )


@pytest.mark.asyncio
async def test_password_reset_confirm_rejects_short_password_at_api_boundary() -> None:
    service = AsyncMock()

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "valid-looking-token",
                "new_password": "short",
            },
        )

    assert response.status_code == 422
    service.confirm_password_reset.assert_not_awaited()


@pytest.mark.asyncio
async def test_password_reset_endpoints_require_no_authenticated_session() -> None:
    service = AsyncMock()

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        request_response = await client.post(
            "/auth/password-reset/request",
            json={"email": "user@example.com"},
        )

        confirm_response = await client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "reset-token",
                "new_password": "New-Secure-Password-2026!",
            },
        )

    assert request_response.status_code == 202
    assert confirm_response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_context_returns_bound_email_without_token():
    service = AsyncMock()
    service.get_password_reset_context.return_value = type(
        "PasswordResetContext",
        (),
        {"email": "real-user@example.com"},
    )()

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/auth/password-reset/context",
            params={"token": "raw-reset-token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "email": "real-user@example.com",
    }
    assert "raw-reset-token" not in response.text
    assert response.headers["cache-control"] == "no-store"

    service.get_password_reset_context.assert_awaited_once_with(
        token="raw-reset-token",
    )


@pytest.mark.asyncio
async def test_password_reset_context_rejects_invalid_token_without_sensitive_data():
    service = AsyncMock()
    service.get_password_reset_context.side_effect = AuthenticationError(
        "Invalid or expired password reset token."
    )

    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/auth/password-reset/context",
            params={"token": "expired-token"},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid or expired password reset token.",
    }
    assert response.headers["cache-control"] == "no-store"
    assert "password_hash" not in response.text
    assert "expired-token" not in response.text


@pytest.mark.asyncio
async def test_password_reset_context_requires_a_token():
    service = AsyncMock()
    app = _create_app(service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/auth/password-reset/context",
        )

    assert response.status_code == 422
    service.get_password_reset_context.assert_not_awaited()
