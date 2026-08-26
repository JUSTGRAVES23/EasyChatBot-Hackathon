from __future__ import annotations

import pytest

from backend.app.application.health.dependency_checks import (
    AsyncDependencyCheck,
    ConfigurationCheck,
)
from backend.app.application.health.operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSeverity,
    OperationalSurface,
)
from backend.app.application.health.operational_event_service import (
    OperationalEventService,
)
from backend.app.application.health.operational_health_snapshot import (
    OperationalHealthSnapshotService,
)
from backend.app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from backend.app.application.health.production_readiness_service import (
    ProductionReadinessService,
)
from backend.app.application.operations_center.announcement_group_operations_api import (
    AnnouncementGroupOperationsAPI,
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

    api = AnnouncementGroupOperationsAPI(
        dashboard_service=dashboard,
        event_service=events,
    )

    return api, events


@pytest.mark.asyncio
async def test_ws21_18_returns_fresh_announcement_group_snapshot():
    api, _events = make_api()

    first = await api.get_details()
    second = await api.get_details()

    assert first["surface"] == "announcement_group"
    assert first["status"] == "healthy"
    assert first["health_score"] == 100

    assert first["generated_at"] != second["generated_at"]


@pytest.mark.asyncio
async def test_ws21_18_exposes_announcement_incidents_and_events_only():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.TELEGRAM_FAILURE,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="announcement-001",
            severity=OperationalSeverity.HIGH,
        )
    )

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.MESSAGE_FAILURE,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="private-001",
            severity=OperationalSeverity.HIGH,
        )
    )

    result = await api.get_details()

    assert result["incidents"]["summary"]["total"] == 1

    assert len(result["incidents"]["items"]) == 1

    assert (
        result["incidents"]["items"][0]["surface"]
        == "announcement_group"
    )

    assert len(result["events"]) == 1

    assert (
        result["events"][0]["surface"]
        == "announcement_group"
    )


@pytest.mark.asyncio
async def test_ws21_18_contains_dependency_and_metric_details():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.TELEGRAM_FAILURE,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="telegram-001",
        )
    )

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.RATE_LIMIT,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="rate-001",
        )
    )

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.ABUSE,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="abuse-001",
        )
    )

    result = await api.get_details()

    assert {
        item["name"]
        for item in result["dependencies"]
    } == {
        "telegram",
        "postgresql",
        "llm_provider",
    }

    assert result["metrics"] == {
        "message_failures": 0,
        "rate_limit_events": 1,
        "abuse_events": 1,
    }


@pytest.mark.asyncio
async def test_ws21_18_does_not_expose_sensitive_event_metadata():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.TELEGRAM_FAILURE,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="safe-001",
            metadata={
                "message": "PRIVATE MESSAGE CONTENT",
                "prompt": "PRIVATE PROMPT",
                "response": "PRIVATE AI RESPONSE",
                "api_key": "SECRET",
                "safe_status": "timeout",
            },
        )
    )

    result = await api.get_details()

    payload = str(result).lower()

    assert "private message content" not in payload
    assert "private prompt" not in payload
    assert "private ai response" not in payload
    assert "secret" not in payload

    assert "safe_status" in payload


@pytest.mark.asyncio
async def test_ws21_18_empty_state_is_safe():
    api, _events = make_api()

    result = await api.get_details()

    assert result["incidents"]["summary"]["total"] == 0
    assert result["incidents"]["items"] == []
    assert result["events"] == []


@pytest.mark.asyncio
async def test_ws21_18_preserves_announcement_surface():
    api, events = make_api()

    events.record_event(
        OperationalEvent(
            event_type=OperationalEventType.TELEGRAM_FAILURE,
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
            correlation_id="announcement-002",
            severity=OperationalSeverity.MEDIUM,
        )
    )

    result = await api.get_details()

    assert result["surface"] == "announcement_group"

    assert all(
        item["surface"] == "announcement_group"
        for item in result["incidents"]["items"]
    )

    assert all(
        event["surface"] == "announcement_group"
        for event in result["events"]
    )