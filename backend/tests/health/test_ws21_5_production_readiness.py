from __future__ import annotations

import pytest

from app.application.health.dependency_checks import (
    AsyncDependencyCheck,
    ConfigurationCheck,
)
from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
)
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)


@pytest.mark.asyncio
async def test_all_dependencies_healthy_produces_ready_result():
    async def healthy():
        return True

    service = ProductionReadinessService(
        checks=(
            ConfigurationCheck(name="telegram", configured=True),
            AsyncDependencyCheck(name="postgresql", probe=healthy),
            AsyncDependencyCheck(name="llm_provider", probe=healthy),
        )
    )

    result = await service.check()

    assert result.ready is True
    assert result.status is HealthStatus.HEALTHY
    assert all(
        check.status is HealthStatus.HEALTHY
        for check in result.checks
    )


@pytest.mark.asyncio
async def test_postgresql_failure_makes_system_not_ready():
    async def failing_database():
        raise RuntimeError("database password=SECRET")

    service = ProductionReadinessService(
        checks=(
            AsyncDependencyCheck(
                name="postgresql",
                probe=failing_database,
            ),
            ConfigurationCheck(name="telegram", configured=True),
        )
    )

    result = await service.check()

    assert result.ready is False
    database = next(
        check for check in result.checks if check.name == "postgresql"
    )

    assert database.status is HealthStatus.UNHEALTHY
    assert "SECRET" not in str(result.as_dict())
    assert "password" not in str(result.as_dict()).lower()


@pytest.mark.asyncio
async def test_llm_failure_does_not_hide_other_dependency_results():
    async def failing_llm():
        raise RuntimeError("provider api_key=SECRET")

    async def healthy():
        return True

    service = ProductionReadinessService(
        checks=(
            ConfigurationCheck(name="telegram", configured=True),
            AsyncDependencyCheck(name="postgresql", probe=healthy),
            AsyncDependencyCheck(name="llm_provider", probe=failing_llm),
        )
    )

    result = await service.check()

    assert result.ready is False
    assert {check.name for check in result.checks} == {
        "telegram",
        "postgresql",
        "llm_provider",
    }
    assert "SECRET" not in str(result.as_dict())


@pytest.mark.asyncio
async def test_missing_telegram_configuration_is_not_ready():
    service = ProductionReadinessService(
        checks=(
            ConfigurationCheck(name="telegram", configured=False),
            ConfigurationCheck(name="postgresql", configured=True),
        )
    )

    result = await service.check()

    assert result.ready is False

    telegram = next(
        check for check in result.checks if check.name == "telegram"
    )

    assert telegram.status is HealthStatus.NOT_CONFIGURED
    assert telegram.details == {"configured": False}


@pytest.mark.asyncio
async def test_empty_check_set_is_not_ready():
    service = ProductionReadinessService(checks=())

    result = await service.check()

    assert result.ready is False
    assert result.status is HealthStatus.UNHEALTHY
    assert result.checks == ()


@pytest.mark.asyncio
async def test_one_broken_check_does_not_stop_remaining_checks():
    calls: list[str] = []

    async def broken():
        calls.append("broken")
        raise RuntimeError("internal failure")

    async def healthy():
        calls.append("healthy")
        return True

    service = ProductionReadinessService(
        checks=(
            AsyncDependencyCheck(name="broken_dependency", probe=broken),
            AsyncDependencyCheck(name="healthy_dependency", probe=healthy),
        )
    )

    result = await service.check()

    assert calls == ["broken", "healthy"]
    assert result.ready is False

    statuses = {
        check.name: check.status
        for check in result.checks
    }

    assert statuses["broken_dependency"] is HealthStatus.UNHEALTHY
    assert statuses["healthy_dependency"] is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_health_result_can_be_returned_directly_by_probe():
    async def probe():
        return HealthCheckResult(
            name="postgresql",
            status=HealthStatus.HEALTHY,
            details={"connectivity": "ok"},
        )

    service = ProductionReadinessService(
        checks=(
            AsyncDependencyCheck(name="postgresql", probe=probe),
        )
    )

    result = await service.check()

    assert result.ready is True
    assert result.checks[0].details == {"connectivity": "ok"}


@pytest.mark.asyncio
async def test_configuration_values_are_never_exposed():
    secret = "super-secret-token"

    service = ProductionReadinessService(
        checks=(
            ConfigurationCheck(
                name="telegram",
                configured=bool(secret),
            ),
        )
    )

    result = await service.check()

    assert result.as_dict() == {
        "status": "healthy",
        "ready": True,
        "checks": {
            "telegram": {
                "status": "healthy",
                "details": {"configured": True},
            }
        },
    }

    assert secret not in str(result.as_dict())


@pytest.mark.asyncio
async def test_dependency_check_failure_is_safe_and_generic():
    async def failing():
        raise RuntimeError(
            "DATABASE_URL=postgresql://user:password@host/db"
        )

    check = AsyncDependencyCheck(
        name="postgresql",
        probe=failing,
    )

    result = await check.check()

    assert result.status is HealthStatus.UNHEALTHY
    assert result.details == {
        "reason": "dependency_check_failed",
    }


@pytest.mark.asyncio
async def test_recovery_after_dependency_becomes_healthy():
    state = {"healthy": False}

    async def recoverable_probe():
        return state["healthy"]

    service = ProductionReadinessService(
        checks=(
            AsyncDependencyCheck(
                name="postgresql",
                probe=recoverable_probe,
            ),
        )
    )

    first = await service.check()
    assert first.ready is False

    state["healthy"] = True

    second = await service.check()

    assert second.ready is True
    assert second.checks[0].status is HealthStatus.HEALTHY
