from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.authentication import router as authentication_router
from app.main import create_application, lifespan


def test_authentication_router_defines_required_endpoints() -> None:
    """The canonical authentication router exposes all required endpoints."""

    route_paths = {
        route.path
        for route in authentication_router.routes
        if hasattr(route, "path")
    }

    assert route_paths == {
        "/auth/register",
        "/auth/login",
        "/auth/password-reset/request",
        "/auth/password-reset/confirm",
        "/auth/password-reset/context",
        "/auth/verify-email",
        "/auth/logout",
        "/auth/session",
    }


def test_create_application_composes_authentication_repository() -> None:
    """Application composition creates the auth repository from the canonical session factory."""

    fake_engine = MagicMock(name="auth_engine")
    fake_session_factory = MagicMock(name="auth_session_factory")

    with (
        patch(
            "app.main.create_async_database_engine",
            return_value=fake_engine,
        ),
        patch(
            "app.main.create_async_session_factory",
            return_value=fake_session_factory,
        ),
        patch(
            "app.main.PostgreSQLAuthenticationRepository",
        ) as repository_factory,
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=MagicMock(),
        ),
    ):
        application = create_application()

    repository_factory.assert_called_once_with(
        fake_session_factory,
    )

    assert application.state.auth_engine is fake_engine
    assert application.state.auth_repository is (
        repository_factory.return_value
    )


def test_create_application_composes_authentication_router() -> None:
    """Application composition explicitly registers the canonical auth router."""

    fake_engine = MagicMock(name="auth_engine")
    fake_session_factory = MagicMock(name="auth_session_factory")

    with (
        patch(
            "app.main.create_async_database_engine",
            return_value=fake_engine,
        ),
        patch(
            "app.main.create_async_session_factory",
            return_value=fake_session_factory,
        ),
        patch(
            "app.main.PostgreSQLAuthenticationRepository",
        ),
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=MagicMock(),
        ),
        patch(
            "app.main.FastAPI.include_router",
        ) as include_router,
    ):
        create_application()

    registered_routers = [
        call.args[0]
        for call in include_router.call_args_list
        if call.args
    ]

    assert authentication_router in registered_routers


@pytest.mark.asyncio
async def test_authentication_engine_is_disposed_by_application_lifespan() -> None:
    """The application-owned PostgreSQL engine is disposed during shutdown."""

    application = MagicMock()

    scheduler_runtime = AsyncMock()
    auth_engine = AsyncMock()

    application.state.scheduler_runtime = scheduler_runtime
    application.state.auth_engine = auth_engine
    application.state.announcement_telegram_client = None

    async with lifespan(application):
        pass

    scheduler_runtime.start.assert_awaited_once()
    scheduler_runtime.stop.assert_awaited_once()
    auth_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_does_not_require_telegram_client() -> None:
    """Authentication engine lifecycle remains valid without Academy Telegram."""

    application = MagicMock()

    scheduler_runtime = AsyncMock()
    auth_engine = AsyncMock()

    application.state.scheduler_runtime = scheduler_runtime
    application.state.auth_engine = auth_engine

    del application.state.announcement_telegram_client

    async with lifespan(application):
        pass

    scheduler_runtime.start.assert_awaited_once()
    scheduler_runtime.stop.assert_awaited_once()
    auth_engine.dispose.assert_awaited_once()
