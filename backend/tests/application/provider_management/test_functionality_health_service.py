from unittest.mock import AsyncMock

import pytest

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
    ProductionReadinessResult,
)
from app.application.provider_management.functionality_health_service import (
    FunctionalityHealthService,
)


def _readiness_service(
    checks: tuple[HealthCheckResult, ...],
) -> AsyncMock:
    service = AsyncMock()

    service.check.return_value = ProductionReadinessResult(
        status=HealthStatus.HEALTHY,
        checks=checks,
    )

    return service


@pytest.mark.asyncio
async def test_llm_provider_health_reaches_conversation_functionality() -> None:
    """An existing LLM health result reaches the functionality projection."""

    readiness_service = _readiness_service(
        (
            HealthCheckResult(
                name="llm_provider",
                status=HealthStatus.HEALTHY,
                details={
                    "provider": "openai",
                    "model": "gpt-5-mini",
                    "reachable": True,
                },
            ),
        )
    )

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
    ).get_health()

    conversation = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "conversation"
    )

    assert conversation["status"] == "healthy"
    assert conversation["provider"] == "openai"
    assert conversation["model"] == "gpt-5-mini"


@pytest.mark.asyncio
async def test_unobserved_functionality_is_unknown() -> None:
    """Missing health telemetry must never be presented as healthy."""

    readiness_service = _readiness_service(())

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
    ).get_health()

    voice = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "voice_tts"
    )

    assert voice["status"] == "unknown"
    assert voice["health_score"] is None


@pytest.mark.asyncio
async def test_health_payload_contains_required_dashboard_fields() -> None:
    """Protect the read-only dashboard contract consumed by the frontend."""

    readiness_service = _readiness_service(())

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
    ).get_health()

    assert "generated_at" in payload
    assert "platform_health" in payload
    assert "user_impact" in payload
    assert "counts" in payload
    assert "functionalities" in payload
    assert "attention" in payload

    assert isinstance(payload["functionalities"], list)
    assert isinstance(payload["attention"], list)
    assert isinstance(payload["counts"], dict)


@pytest.mark.asyncio
async def test_unhealthy_provider_is_reported_as_incident() -> None:
    """An unhealthy provider creates an operational attention signal."""

    readiness_service = _readiness_service(
        (
            HealthCheckResult(
                name="llm_provider",
                status=HealthStatus.UNHEALTHY,
                details={
                    "provider": "openai",
                    "reason": "provider_unavailable",
                },
            ),
        )
    )

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
    ).get_health()

    conversation = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "conversation"
    )

    assert conversation["status"] == "unavailable"
    assert conversation["health_score"] == 0.0
    assert conversation["risk_level"] == "high"
    assert conversation in payload["attention"]

    assert payload["platform_health"] == "incident"
    assert payload["user_impact"] == "high"


@pytest.mark.asyncio
async def test_telegram_health_reaches_telegram_functionality() -> None:
    """Telegram dependency health maps to the Telegram functionality."""

    readiness_service = _readiness_service(
        (
            HealthCheckResult(
                name="telegram",
                status=HealthStatus.HEALTHY,
                details={
                    "provider": "telegram",
                    "reachable": True,
                },
            ),
        )
    )

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
    ).get_health()

    telegram = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "telegram"
    )

    assert telegram["status"] == "healthy"
    assert telegram["health_score"] == 100.0
    assert telegram["risk_level"] == "low"
    assert telegram["provider"] == "telegram"


@pytest.mark.asyncio
async def test_database_health_reaches_database_functionality() -> None:
    """PostgreSQL dependency health maps to the database functionality."""

    readiness_service = _readiness_service(
        (
            HealthCheckResult(
                name="postgresql",
                status=HealthStatus.HEALTHY,
                details={
                    "provider": "postgresql",
                    "reachable": True,
                },
            ),
        )
    )

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
    ).get_health()

    database = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "database"
    )

    assert database["status"] == "healthy"
    assert database["health_score"] == 100.0
    assert database["risk_level"] == "low"
    assert database["provider"] == "postgresql"


def test_health_service_requires_a_readiness_service() -> None:
    """Fail fast instead of creating an unconnected health source."""

    with pytest.raises(
        ValueError,
        match="readiness_service",
    ):
        FunctionalityHealthService(
            readiness_service=None,
        )

class _HealthControlService:
    def __init__(self, availability="enabled"):
        self.availability = availability

    def get_availability(self, *, environment, functionality_id):
        return self.availability


@pytest.mark.asyncio
async def test_disabled_control_state_reaches_functionality_health() -> None:
    readiness_service = _readiness_service(
        (
            HealthCheckResult(
                name="llm_provider",
                status=HealthStatus.HEALTHY,
                details={"provider": "openai"},
            ),
        )
    )

    control_service = _HealthControlService("disabled")

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
        functionality_control_service=control_service,
    ).get_health()

    conversation = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "conversation"
    )

    assert conversation["status"] == "healthy"
    assert conversation["availability"] == "disabled"


@pytest.mark.asyncio
async def test_enabled_control_state_reaches_functionality_health() -> None:
    readiness_service = _readiness_service(
        (
            HealthCheckResult(
                name="llm_provider",
                status=HealthStatus.HEALTHY,
                details={"provider": "openai"},
            ),
        )
    )

    control_service = _HealthControlService("enabled")

    payload = await FunctionalityHealthService(
        readiness_service=readiness_service,
        functionality_control_service=control_service,
    ).get_health()

    conversation = next(
        item
        for item in payload["functionalities"]
        if item["functionality_id"] == "conversation"
    )

    assert conversation["status"] == "healthy"
    assert conversation["availability"] == "enabled"


