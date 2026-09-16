"""
M0F application entrypoint architecture regression tests.

These tests protect the public application entrypoints and the controlled
Telegram runtime lifecycle.

Architecture boundary:

    Repository Architecture Test
            |
            +--> backend application boundary
                         |
                         +--> app.main.create_application()
                         |
                         +--> api.main.create_app()
                                      |
                                      +--> controlled
                                           functionality-control lifecycle
                                      |
                                      +--> controlled
                                           Telegram runtime lifecycle

This test lives at repository level because it verifies the application
composition boundary rather than a single backend implementation package.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI


# Repository-level architecture tests must explicitly establish the backend
# application import boundary. This prevents the repository-root `app`
# directory, if present, from shadowing the authoritative backend package.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"

if not BACKEND_ROOT.is_dir():
    raise RuntimeError(
        f"Expected backend application root does not exist: {BACKEND_ROOT}"
    )

backend_path = str(BACKEND_ROOT)

if backend_path in sys.path:
    sys.path.remove(backend_path)

sys.path.insert(0, backend_path)


def test_app_main_create_application_returns_fastapi() -> None:
    """The primary application entrypoint must create a FastAPI application."""
    from app.main import create_application

    application = create_application()

    assert isinstance(application, FastAPI)


def test_api_main_create_app_returns_fastapi() -> None:
    """The API application entrypoint must create a FastAPI application."""
    from api.main import create_app

    application = create_app()

    assert isinstance(application, FastAPI)


def test_api_main_lifespan_is_async_context_manager() -> None:
    """
    The API lifecycle must be implemented with an async context manager.

    The @asynccontextmanager decorator turns the underlying async-generator
    function into a callable factory. The factory itself does not expose
    __aenter__ / __aexit__; calling it with the application produces the
    async context-manager object.

    This test therefore verifies both layers:

        lifespan.__wrapped__
            -> async-generator implementation

        lifespan(application)
            -> async context manager
    """
    from api.main import lifespan

    wrapped = getattr(lifespan, "__wrapped__", None)

    assert wrapped is not None
    assert inspect.isasyncgenfunction(wrapped)

    application = FastAPI()
    context_manager = lifespan(application)

    assert hasattr(context_manager, "__aenter__")
    assert hasattr(context_manager, "__aexit__")
    assert inspect.iscoroutinefunction(context_manager.__aenter__)
    assert inspect.iscoroutinefunction(context_manager.__aexit__)


@pytest.mark.asyncio
async def test_api_main_lifespan_controls_runtime_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify the controlled functionality-control and Telegram runtime lifecycle.

    Startup:
        bootstrap application
        create functionality-control service/engine
        store them on application.state
        start Telegram runtime with the control service

    Shutdown:
        stop Telegram runtime
        dispose functionality-control engine
        clear application state
    """
    import api.main

    application = FastAPI()

    events: list[object] = []

    class FakeControlEngine:
        def dispose(self) -> None:
            events.append("dispose")

    control_service = object()
    control_engine = FakeControlEngine()

    def fake_bootstrap_application() -> None:
        events.append("bootstrap")

    def fake_create_standalone_functionality_control_service():
        events.append("create_control_service")
        return control_service, control_engine

    async def fake_start_telegram_runtime(
        *,
        functionality_control_service,
    ) -> None:
        events.append(
            ("start_telegram_runtime", functionality_control_service)
        )

    async def fake_stop_telegram_runtime() -> None:
        events.append("stop_telegram_runtime")

    monkeypatch.setattr(
        api.main,
        "bootstrap_application",
        fake_bootstrap_application,
    )
    monkeypatch.setattr(
        api.main,
        "create_standalone_functionality_control_service",
        fake_create_standalone_functionality_control_service,
    )
    monkeypatch.setattr(
        api.main,
        "start_telegram_runtime",
        fake_start_telegram_runtime,
    )
    monkeypatch.setattr(
        api.main,
        "stop_telegram_runtime",
        fake_stop_telegram_runtime,
    )

    async with api.main.lifespan(application):
        assert (
            application.state.functionality_control_service
            is control_service
        )
        assert (
            application.state.functionality_control_engine
            is control_engine
        )

        assert events == [
            "bootstrap",
            "create_control_service",
            ("start_telegram_runtime", control_service),
        ]

    assert events == [
        "bootstrap",
        "create_control_service",
        ("start_telegram_runtime", control_service),
        "stop_telegram_runtime",
        "dispose",
    ]

    assert application.state.functionality_control_service is None
    assert application.state.functionality_control_engine is None