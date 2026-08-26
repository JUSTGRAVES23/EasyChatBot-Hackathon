from __future__ import annotations

import pytest

from app.application.health.dependency_checks import (
    AsyncDependencyCheck,
    ConfigurationCheck,
)
from app.application.health.health_result import (
    HealthStatus,
)
from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSeverity,
    OperationalSurface,
)
from app.application.health.operational_event_service import (
    OperationalEventService,
)
from app.application.health.operational_health_snapshot import (
    OperationalHealthSnapshotService,
)
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)


async def healthy_probe():
    return True


def make_readiness():
    return ProductionReadinessService(
        checks=(
            ConfigurationCheck(
                name="telegram",
                configured=True,
            ),
            AsyncDependencyCheck(
                name="postgresql",
                probe=healthy_probe,
            ),
            AsyncDependencyCheck(
                name="llm_provider",
                probe=healthy_probe,
            ),
        )
    )


def make_service():
    health_service = (
        OperationalHealthSnapshotService(
            readiness_service=make_readiness()
        )
    )

    event_service = (
        OperationalEventService()
    )

    return (
        OperationalDashboardService(
            health_snapshot_service=(
                health_service
            ),
            event_service=event_service,
        ),
        event_service,
    )


@pytest.mark.asyncio
async def test_ws21_10_produces_complete_dashboard_contract():

    service, _events = make_service()

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    payload = snapshot.as_dict()

    assert "generated_at" in payload
    assert "overall" in payload
    assert "private_classroom" in payload
    assert "announcement_group" in payload
    assert "incidents" in payload

    assert (
        payload["overall"]["status"]
        == "healthy"
    )

    assert (
        payload["overall"]["health_score"]
        == 100
    )


@pytest.mark.asyncio
async def test_ws21_10_private_classroom_contains_dependencies():

    service, _events = make_service()

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    private = (
        snapshot.private_classroom
    )

    dependency_names = {
        dependency.name
        for dependency
        in private.dependencies
    }

    assert "telegram" in dependency_names
    assert "postgresql" in dependency_names
    assert "llm_provider" in dependency_names


@pytest.mark.asyncio
async def test_ws21_10_announcement_group_is_separate():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType
                .NOTIFICATION_FAILURE
            ),
            surface=(
                OperationalSurface
                .ANNOUNCEMENT_GROUP
            ),
            correlation_id="announcement-001",
            severity=(
                OperationalSeverity.HIGH
            ),
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    assert (
        snapshot.announcement_group
        .surface
        is OperationalSurface.ANNOUNCEMENT_GROUP
    )

    assert (
        snapshot.announcement_group
        .incidents.total
        == 1
    )

    assert (
        snapshot.private_classroom
        .incidents.total
        == 0
    )


@pytest.mark.asyncio
async def test_ws21_10_private_operational_metrics_are_exposed():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType.MESSAGE_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="message-001",
        )
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType.RATE_LIMIT
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="rate-001",
        )
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType.ABUSE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="abuse-001",
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    metrics = (
        snapshot.private_classroom
        .metrics
    )

    assert metrics.message_failures == 1
    assert metrics.rate_limit_events == 1
    assert metrics.abuse_events == 1


@pytest.mark.asyncio
async def test_ws21_10_incident_severity_counts():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType
                .DATABASE_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="critical-001",
            severity=(
                OperationalSeverity.CRITICAL
            ),
        )
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType.PROVIDER_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="high-001",
            severity=(
                OperationalSeverity.HIGH
            ),
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    summary = (
        snapshot.private_classroom
        .incidents
    )

    assert summary.total == 2
    assert summary.open == 2
    assert summary.critical == 1
    assert summary.high == 1


@pytest.mark.asyncio
async def test_ws21_10_incident_includes_investigation_fields():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType.MESSAGE_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="investigate-001",
            severity=(
                OperationalSeverity.HIGH
            ),
            user_reference="user-ref-001",
            world_id="world-fr",
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    assert len(
        snapshot.incidents
    ) == 1

    incident = snapshot.incidents[0]

    assert (
        incident.correlation_id
        == "investigate-001"
    )

    assert (
        incident.user_reference
        == "user-ref-001"
    )

    assert (
        incident.world_id
        == "world-fr"
    )


@pytest.mark.asyncio
async def test_ws21_10_dashboard_contract_exposes_no_learner_content():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType.MESSAGE_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="safe-001",
            metadata={
                "message": (
                    "PRIVATE LEARNER CONTENT"
                ),
                "prompt": (
                    "PRIVATE PROMPT"
                ),
                "response": (
                    "PRIVATE AI RESPONSE"
                ),
                "safe_status": "timeout",
            },
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    payload = str(
        snapshot.as_dict()
    )

    assert (
        "PRIVATE LEARNER CONTENT"
        not in payload
    )

    assert (
        "PRIVATE PROMPT"
        not in payload
    )

    assert (
        "PRIVATE AI RESPONSE"
        not in payload
    )


@pytest.mark.asyncio
async def test_ws21_10_dashboard_contract_contains_no_secrets():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType
                .PROVIDER_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="secret-001",
            metadata={
                "api_key": "SUPER-SECRET",
                "password": "PASSWORD-SECRET",
                "database_url": (
                    "postgresql://secret"
                ),
            },
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    payload = str(
        snapshot.as_dict()
    ).lower()

    assert "super-secret" not in payload
    assert "password-secret" not in payload
    assert "postgresql://secret" not in payload


@pytest.mark.asyncio
async def test_ws21_10_critical_incident_reduces_health_score():

    service, event_service = (
        make_service()
    )

    event_service.record_event(
        OperationalEvent(
            event_type=(
                OperationalEventType
                .DATABASE_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="critical-001",
            severity=(
                OperationalSeverity.CRITICAL
            ),
        )
    )

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    assert (
        snapshot.overall_status
        is HealthStatus.HEALTHY
    )

    assert (
        snapshot.health_score
        == 80
    )


@pytest.mark.asyncio
async def test_ws21_10_dashboard_snapshot_is_read_only():

    service, _events = make_service()

    first = (
        await service.create_dashboard_snapshot()
    )

    second = (
        await service.create_dashboard_snapshot()
    )

    assert (
        first.private_classroom
        .incidents.total
        == second.private_classroom
        .incidents.total
    )

    assert (
        first.announcement_group
        .incidents.total
        == second.announcement_group
        .incidents.total
    )


@pytest.mark.asyncio
async def test_ws21_10_dashboard_contract_is_serializable():

    service, _events = make_service()

    snapshot = (
        await service.create_dashboard_snapshot()
    )

    payload = snapshot.as_dict()

    assert isinstance(payload, dict)

    assert isinstance(
        payload["incidents"],
        list,
    )

    assert isinstance(
        payload["private_classroom"],
        dict,
    )

    assert isinstance(
        payload["announcement_group"],
        dict,
    )

    assert isinstance(
        payload["overall"],
        dict,
    )