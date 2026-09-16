import inspect

import pytest
from fastapi import FastAPI


def test_current_platform_application_is_fastapi_application():
    from app.main import create_application

    application = create_application()

    assert isinstance(application, FastAPI)


def test_runtime_api_application_is_fastapi_application():
    from api.main import create_app

    application = create_app()

    assert isinstance(application, FastAPI)


@pytest.mark.asyncio
async def test_runtime_api_lifespan_executes_bootstrap_and_shutdown():
    import api.main as runtime_main

    calls: list[str] = []

    class FakeFunctionalityControlService:
        pass

    class FakeFunctionalityControlEngine:
        def dispose(self):
            calls.append("dispose_control_engine")

    control_service = FakeFunctionalityControlService()
    control_engine = FakeFunctionalityControlEngine()

    def fake_bootstrap_application():
        calls.append("bootstrap")

    def fake_create_standalone_functionality_control_service():
        calls.append("create_control_service")
        return control_service, control_engine

    async def fake_start_telegram_runtime(
        *,
        functionality_control_service,
    ):
        calls.append("start_telegram")
        assert functionality_control_service is control_service

    async def fake_stop_telegram_runtime():
        calls.append("stop_telegram")

    runtime_main.bootstrap_application = fake_bootstrap_application
    runtime_main.create_standalone_functionality_control_service = (
        fake_create_standalone_functionality_control_service
    )
    runtime_main.start_telegram_runtime = fake_start_telegram_runtime
    runtime_main.stop_telegram_runtime = fake_stop_telegram_runtime

    application = FastAPI()

    async with runtime_main.lifespan(application):
        assert calls == [
            "bootstrap",
            "create_control_service",
            "start_telegram",
        ]

        assert (
            application.state.functionality_control_service
            is control_service
        )

        assert (
            application.state.functionality_control_engine
            is control_engine
        )

    assert calls == [
        "bootstrap",
        "create_control_service",
        "start_telegram",
        "stop_telegram",
        "dispose_control_engine",
    ]

    assert application.state.functionality_control_service is None

    assert application.state.functionality_control_engine is None


def test_runtime_api_lifespan_is_async_context_manager_factory():
    from api.main import lifespan

    context_manager = lifespan(FastAPI())

    assert hasattr(context_manager, "__aenter__")
    assert hasattr(context_manager, "__aexit__")


def test_runtime_api_lifespan_preserves_async_generator_implementation():
    from api.main import lifespan

    wrapped = getattr(lifespan, "__wrapped__", None)

    assert wrapped is not None
    assert inspect.isasyncgenfunction(wrapped)