from __future__ import annotations

from datetime import datetime

import pytest

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
    ProductionReadinessResult,
)
from app.project_control_center.domain.models import SourceStatus
from app.project_control_center.infrastructure.health_source import (
    ProductionHealthProjectStatusSource,
)


class FakeProductionHealthService:
    def __init__(
        self,
        *,
        result: ProductionReadinessResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls = 0

    async def check_production_health(
        self,
    ) -> ProductionReadinessResult:
        self.calls += 1

        if self.error is not None:
            raise self.error

        assert self.result is not None
        return self.result


def make_result(
    status: HealthStatus,
) -> ProductionReadinessResult:
    return ProductionReadinessResult(
        status=status,
        checks=(
            HealthCheckResult(
                name="postgresql",
                status=status,
                details=(
                    {"connectivity": "ok"}
                    if status is HealthStatus.HEALTHY
                    else {"reason": "database_unavailable"}
                ),
            ),
        ),
    )


@pytest.mark.asyncio
async def test_healthy_production_health_is_available():
    service = FakeProductionHealthService(
        result=make_result(HealthStatus.HEALTHY),
    )

    source = ProductionHealthProjectStatusSource(
        health_service=service,
    )

    snapshot = await source.fetch_health()

    assert service.calls == 1
    assert snapshot.source_id == "production-health"
    assert snapshot.name == "Production Health"
    assert snapshot.status is SourceStatus.AVAILABLE
    assert snapshot.error is None
    assert isinstance(snapshot.updated_at, datetime)


@pytest.mark.asyncio
async def test_unhealthy_production_health_is_unavailable():
    service = FakeProductionHealthService(
        result=make_result(HealthStatus.UNHEALTHY),
    )

    source = ProductionHealthProjectStatusSource(
        health_service=service,
    )

    snapshot = await source.fetch_health()

    assert snapshot.status is SourceStatus.UNAVAILABLE
    assert snapshot.error == "production_health_not_ready"


@pytest.mark.asyncio
async def test_not_configured_production_health_is_unavailable():
    service = FakeProductionHealthService(
        result=make_result(HealthStatus.NOT_CONFIGURED),
    )

    source = ProductionHealthProjectStatusSource(
        health_service=service,
    )

    snapshot = await source.fetch_health()

    assert snapshot.status is SourceStatus.UNAVAILABLE
    assert snapshot.error == "production_health_not_ready"


@pytest.mark.asyncio
async def test_health_service_failure_is_safe_and_generic():
    service = FakeProductionHealthService(
        error=RuntimeError(
            "DATABASE_URL=postgresql://user:password@host/db"
        ),
    )

    source = ProductionHealthProjectStatusSource(
        health_service=service,
    )

    snapshot = await source.fetch_health()

    assert snapshot.status is SourceStatus.UNAVAILABLE
    assert snapshot.error == "production_health_check_failed"

    serialized = str(snapshot)

    assert "password" not in serialized
    assert "postgresql://" not in serialized


def test_health_does_not_probe_external_dependencies():
    service = FakeProductionHealthService()

    source = ProductionHealthProjectStatusSource(
        health_service=service,
    )

    snapshot = source.health()

    assert snapshot.source_id == "production-health"
    assert snapshot.name == "Production Health"
    assert snapshot.status is SourceStatus.AVAILABLE
    assert service.calls == 0


@pytest.mark.asyncio
async def test_adapter_does_not_duplicate_project_status_data():
    service = FakeProductionHealthService(
        result=make_result(HealthStatus.HEALTHY),
    )

    source = ProductionHealthProjectStatusSource(
        health_service=service,
    )

    assert await source.fetch_metrics(
        "easychatbot"
    ) == []

    assert source.fetch_workstreams(
        "easychatbot"
    ) == []

    assert source.fetch_issues(
        "easychatbot"
    ) == []

    assert source.fetch_risks(
        "easychatbot"
    ) == []

    assert source.fetch_actions(
        "easychatbot"
    ) == []

    assert source.fetch_milestones(
        "easychatbot"
    ) == []


def test_none_health_service_is_rejected():
    with pytest.raises(
        ValueError,
        match="health_service cannot be None",
    ):
        ProductionHealthProjectStatusSource(
            health_service=None,
        )
