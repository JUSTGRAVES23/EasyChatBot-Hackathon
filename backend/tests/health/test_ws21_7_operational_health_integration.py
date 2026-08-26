from __future__ import annotations

import pytest

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
)
from app.application.health.production_health_configuration import (
    ProductionHealthConfiguration,
)
from app.application.health.production_health_service import (
    ProductionHealthService,
)


class FakeEngine:
    def connect(self):
        return self

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    def execute(self, statement):
        return None


class FakeTelegramBot:

    def __init__(
        self,
        token,
    ):
        self.token = token

    async def get_me(self):

        class User:
            id = 123

        return User()

    async def shutdown(self):
        pass


async def fake_ollama_get(
    _url,
):
    return type(
        "Response",
        (),
        {
            "status_code": 200,
        },
    )()


@pytest.mark.asyncio
async def test_ws21_7_builds_production_health_graph(
    monkeypatch,
):

    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN",
        "test-token",
    )

    service = ProductionHealthService(
        configuration=ProductionHealthConfiguration(
            database_engine=FakeEngine(),
            telegram_bot_factory=FakeTelegramBot,
            llm_provider="ollama",
            llm_request_get=fake_ollama_get,
        )
    )

    result = await (
        service
        .check_production_health()
    )

    assert result.ready is True

    assert {
        check.name
        for check in result.checks
    } == {
        "postgresql",
        "llm_provider",
        "telegram",
    }


@pytest.mark.asyncio
async def test_ws21_7_keeps_dependency_failures_isolated(
):

    class BrokenCheck:

        name = "broken"

        async def check(self):

            raise RuntimeError(
                "secret=password"
            )

    class HealthyCheck:

        name = "healthy"

        async def check(self):

            return HealthCheckResult(
                name="healthy",
                status=HealthStatus.HEALTHY,
            )

    from app.application.health.production_readiness_service import (
        ProductionReadinessService,
    )

    service = ProductionReadinessService(
        checks=(
            BrokenCheck(),
            HealthyCheck(),
        )
    )

    result = await service.check()

    assert result.ready is False

    assert (
        result.checks[0]
        .details
        ==
        {
            "reason": "health_check_failed"
        }
    )

    assert "password" not in str(
        result.checks
    )


@pytest.mark.asyncio
async def test_ws21_7_result_is_dashboard_ready(
):

    service = ProductionHealthService(
        configuration=ProductionHealthConfiguration(
            database_engine=FakeEngine(),
            telegram_bot_factory=FakeTelegramBot,
            llm_provider="ollama",
            llm_request_get=fake_ollama_get,
        )
    )

    result = await (
        service
        .check_production_health()
    )

    payload = result.as_dict()

    assert "status" in payload
    assert "ready" in payload
    assert "checks" in payload

    assert isinstance(
        payload["checks"],
        dict,
    )