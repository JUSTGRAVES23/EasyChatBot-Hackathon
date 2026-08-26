from __future__ import annotations

import pytest

from app.application.health.dependency_checks import (
    AsyncDependencyCheck,
    ConfigurationCheck,
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
from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)
from app.application.operations_center.private_classroom_operations_api import (
    PrivateClassroomOperationsAPI,
)


async def healthy_probe():
    return True


def make_api():
    readiness = ProductionReadinessService(
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

    health = OperationalHealthSnapshotService(
        readiness_service=readiness,
    )
    events = OperationalEventService()
    dashboard = OperationalDashboardService(
        health_snapshot_service=health,
        event_service=events,
    )

    return PrivateClassroomOperationsAPI(
        dashboard_service=dashboard,
    ), events


@pytest.mark.asyncio
async def test_ws21_17_returns_fresh_private_classroom_snapshot():
    api, _events = make_api()

    first = await api.get_details()
    second = await api.get_details()

    assert first["surface"] == "private_classroom"
    assert first["status"] == "healthy"
    assert first["health_score"] == 100
    assert first["generated_at"] != second["generated_at"]


@pytest.mark.asyncio
async def test_ws21_17_exposes_private_incidents_and_events_only():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.MESSAGE_FAILURE,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="private-001",
            severity=OperationalSeverity.HIGH,
            world_id="world-fr",
        )
    )
    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.TELEGRAM_FAILURE,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="announcement-001",
        )
    )

    result = await api.get_details()

    assert result["incidents"]["summary"]["total"] == 1
    assert len(result["incidents"]["items"]) == 1
    assert result["incidents"]["items"][0]["surface"] == "private_classroom"

    assert len(result["events"]) == 1
    assert result["events"][0]["surface"] == "private_classroom"


@pytest.mark.asyncio
async def test_ws21_17_contains_dependency_and_metric_details():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.MESSAGE_FAILURE,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="message-001",
        )
    )
    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.RATE_LIMIT,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="rate-001",
        )
    )
    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.ABUSE,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="abuse-001",
        )
    )

    result = await api.get_details()

    assert {
        item["name"] for item in result["dependencies"]
    } == {"telegram", "postgresql", "llm_provider"}

    assert result["metrics"] == {
        "message_failures": 1,
        "rate_limit_events": 1,
        "abuse_events": 1,
    }


@pytest.mark.asyncio
async def test_ws21_17_does_not_expose_sensitive_event_metadata():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.MESSAGE_FAILURE,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="safe-001",
            metadata={
                "message": "PRIVATE LEARNER CONTENT",
                "prompt": "PRIVATE PROMPT",
                "response": "PRIVATE AI RESPONSE",
                "api_key": "SECRET",
                "safe_status": "timeout",
            },
        )
    )

    result = await api.get_details()
    payload = str(result).lower()

    assert "private learner content" not in payload
    assert "private prompt" not in payload
    assert "private ai response" not in payload
    assert "secret" not in payload
    assert "safe_status" in payload
