from unittest.mock import AsyncMock

import pytest

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
    ProductionReadinessResult,
)
from app.application.provider_management.environment import OperationsEnvironment
from app.application.provider_management.functionality_health_service import FunctionalityHealthService


def service(*checks: HealthCheckResult) -> AsyncMock:
    result = AsyncMock()
    result.check.return_value = ProductionReadinessResult(
        status=HealthStatus.HEALTHY,
        checks=checks,
    )
    return result


@pytest.mark.asyncio
async def test_legacy_call_defaults_to_adults() -> None:
    payload = await FunctionalityHealthService(
        readiness_service=service(),
    ).get_health()
    assert payload["environment"] == "adults"


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", [OperationsEnvironment.KIDS, OperationsEnvironment.ADULTS])
async def test_environment_is_propagated(environment: OperationsEnvironment) -> None:
    payload = await FunctionalityHealthService(
        readiness_service=service(),
    ).get_health(environment=environment)
    assert payload["environment"] == environment.value
    assert all(item["environment"] == environment.value for item in payload["functionalities"])


@pytest.mark.asyncio
async def test_existing_frontend_contract_fields_are_present() -> None:
    payload = await FunctionalityHealthService(
        readiness_service=service(
            HealthCheckResult(
                name="llm_provider",
                status=HealthStatus.HEALTHY,
                details={"provider": "openai", "model": "gpt-5-mini"},
            )
        ),
    ).get_health(environment=OperationsEnvironment.KIDS)

    item = next(
        x for x in payload["functionalities"]
        if x["functionality_id"] == "conversation"
    )

    assert item["category"] == "AI"
    assert item["description"]
    assert item["capability"] == "conversation"
    assert item["checked_at"] == payload["generated_at"]
    assert item["controllable"] is False
    assert item["reason"]
    assert item["environment"] == "kids"
    assert item["availability"] == "enabled"
    assert item["policy_status"] == "not_evaluated"


@pytest.mark.asyncio
async def test_unhealthy_provider_is_an_incident() -> None:
    payload = await FunctionalityHealthService(
        readiness_service=service(
            HealthCheckResult(
                name="llm_provider",
                status=HealthStatus.UNHEALTHY,
                details={"provider": "openai"},
            )
        ),
    ).get_health()

    item = next(x for x in payload["functionalities"] if x["functionality_id"] == "conversation")
    assert item["status"] == "unavailable"
    assert payload["platform_health"] == "incident"
    assert payload["platform_health_score"] == 0.0


