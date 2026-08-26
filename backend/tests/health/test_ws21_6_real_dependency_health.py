from __future__ import annotations

import os

import pytest

from app.application.health.health_result import HealthStatus
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)
from app.infrastructure.health.llm_provider_health_check import (
    LLMProviderHealthCheck,
)
from app.infrastructure.health.postgresql_health_check import (
    PostgreSQLHealthCheck,
)
from app.infrastructure.health.telegram_health_check import (
    TelegramHealthCheck,
)


class FakeConnection:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        self.calls.append(str(statement))


class FakeEngine:
    def __init__(self):
        self.calls = []
        self.disposed = False

    def connect(self):
        return FakeConnection(self.calls)

    def dispose(self):
        self.disposed = True


@pytest.mark.asyncio
async def test_postgresql_probe_is_read_only():
    engine = FakeEngine()

    result = await PostgreSQLHealthCheck(
        engine=engine
    ).check()

    assert result.status is HealthStatus.HEALTHY
    assert "SELECT 1" in engine.calls[0]
    assert engine.disposed is False


@pytest.mark.asyncio
async def test_postgresql_failure_is_sanitized():
    class BrokenEngine:
        def connect(self):
            raise RuntimeError(
                "postgresql password=SECRET"
            )

    result = await PostgreSQLHealthCheck(
        engine=BrokenEngine()
    ).check()

    assert result.status is HealthStatus.UNHEALTHY
    assert result.details == {
        "reason": "database_unavailable"
    }
    assert "SECRET" not in str(result.details)


@pytest.mark.asyncio
async def test_telegram_missing_token_is_not_configured(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    result = await TelegramHealthCheck().check()

    assert result.status is HealthStatus.NOT_CONFIGURED
    assert result.details == {"configured": False}


@pytest.mark.asyncio
async def test_telegram_probe_uses_get_me_only(monkeypatch):
    calls = []

    class FakeUser:
        id = 123

    class FakeBot:
        def __init__(self, token):
            assert token == "test-token"

        async def get_me(self):
            calls.append("get_me")
            return FakeUser()

        async def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")

    result = await TelegramHealthCheck(
        bot_factory=FakeBot
    ).check()

    assert result.status is HealthStatus.HEALTHY
    assert calls == ["get_me", "shutdown"]
    assert "test-token" not in str(result.details)


@pytest.mark.asyncio
async def test_ollama_probe_does_not_generate():
    calls = []

    class FakeResponse:
        status_code = 200

    async def fake_get(url):
        calls.append(url)
        return FakeResponse()

    result = await LLMProviderHealthCheck(
        provider="ollama",
        request_get=fake_get,
    ).check()

    assert result.status is HealthStatus.HEALTHY
    assert calls == [
        "http://localhost:11434/api/tags"
    ]


@pytest.mark.asyncio
async def test_openai_missing_key_is_not_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = await LLMProviderHealthCheck(
        provider="openai"
    ).check()

    assert result.status is HealthStatus.NOT_CONFIGURED
    assert result.details == {
        "provider": "openai",
        "configured": False,
    }


@pytest.mark.asyncio
async def test_provider_failure_is_sanitized():
    async def failing_get(_url):
        raise RuntimeError(
            "api_key=SUPER_SECRET"
        )

    result = await LLMProviderHealthCheck(
        provider="ollama",
        request_get=failing_get,
    ).check()

    assert result.status is HealthStatus.UNHEALTHY
    assert result.details == {
        "provider": "ollama",
        "reason": "provider_unavailable",
    }
    assert "SUPER_SECRET" not in str(result.details)


@pytest.mark.asyncio
async def test_readiness_runs_all_checks_after_failure():
    class HealthyCheck:
        name = "healthy"

        async def check(self):
            return {
                "name": self.name
            }

    class BrokenCheck:
        name = "broken"

        async def check(self):
            raise RuntimeError("secret")

    # Return proper results while proving aggregation continues.
    from app.application.health.health_result import HealthCheckResult

    class SafeBrokenCheck:
        name = "broken"

        async def check(self):
            raise RuntimeError("secret")

    class SafeHealthyCheck:
        name = "healthy"

        async def check(self):
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
            )

    result = await ProductionReadinessService(
        checks=(
            SafeBrokenCheck(),
            SafeHealthyCheck(),
        )
    ).check()

    assert result.ready is False
    assert [item.name for item in result.checks] == [
        "broken",
        "healthy",
    ]
    assert result.checks[0].details == {
        "reason": "health_check_failed"
    }


@pytest.mark.asyncio
async def test_full_readiness_aggregates_postgres_llm_telegram(
    monkeypatch,
):
    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN",
        "test-token",
    )

    class FakeUser:
        id = 1

    class FakeBot:
        def __init__(self, token):
            pass

        async def get_me(self):
            return FakeUser()

        async def shutdown(self):
            pass

    async def ollama_get(_url):
        return type(
            "Response",
            (),
            {"status_code": 200},
        )()

    engine = FakeEngine()

    service = ProductionReadinessService(
        checks=(
            PostgreSQLHealthCheck(engine=engine),
            LLMProviderHealthCheck(
                provider="ollama",
                request_get=ollama_get,
            ),
            TelegramHealthCheck(
                bot_factory=FakeBot
            ),
        )
    )

    result = await service.check()

    assert result.ready is True
    assert {
        item.name for item in result.checks
    } == {
        "postgresql",
        "llm_provider",
        "telegram",
    }
