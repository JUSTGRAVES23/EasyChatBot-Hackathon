from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.health.operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSeverity,
    OperationalSurface,
)
from app.application.health.operational_event_service import (
    OperationalEventService,
)
from app.application.health.operational_incident import (
    IncidentStatus,
)


def make_event(
    *,
    correlation_id: str = "corr-001",
    event_type: OperationalEventType = (
        OperationalEventType.MESSAGE_FAILURE
    ),
    surface: OperationalSurface = (
        OperationalSurface.PRIVATE_CLASSROOM
    ),
    severity: OperationalSeverity = (
        OperationalSeverity.HIGH
    ),
    user_reference: str | None = "user-ref-001",
    world_id: str | None = "world-fr",
):
    return OperationalEvent(
        event_type=event_type,
        surface=surface,
        correlation_id=correlation_id,
        severity=severity,
        occurred_at=datetime.now(
            timezone.utc
        ),
        user_reference=user_reference,
        world_id=world_id,
    )


def test_ws21_9_event_creates_incident():

    service = OperationalEventService()

    incident = service.record_event(
        make_event()
    )

    assert incident.incident_id
    assert incident.correlation_id == "corr-001"

    assert (
        incident.event_type
        is OperationalEventType.MESSAGE_FAILURE
    )

    assert (
        incident.surface
        is OperationalSurface.PRIVATE_CLASSROOM
    )

    assert (
        incident.severity
        is OperationalSeverity.HIGH
    )

    assert (
        incident.status
        is IncidentStatus.DETECTED
    )

    assert incident.occurrence_count == 1


def test_ws21_9_correlation_aggregates_repeated_events():

    service = OperationalEventService()

    first = service.record_event(
        make_event()
    )

    second = service.record_event(
        make_event()
    )

    assert (
        first.incident_id
        == second.incident_id
    )

    assert second.occurrence_count == 2

    assert len(second.events) == 2


def test_ws21_9_different_correlation_ids_create_separate_incidents():

    service = OperationalEventService()

    first = service.record_event(
        make_event(
            correlation_id="corr-001"
        )
    )

    second = service.record_event(
        make_event(
            correlation_id="corr-002"
        )
    )

    assert (
        first.incident_id
        != second.incident_id
    )

    assert (
        service.list_incidents()
        and len(service.list_incidents())
        == 2
    )


def test_ws21_9_user_and_world_are_associated():

    service = OperationalEventService()

    incident = service.record_event(
        make_event(
            user_reference="telegram-ref-123",
            world_id="world-fr",
        )
    )

    assert (
        incident.user_reference
        == "telegram-ref-123"
    )

    assert incident.world_id == "world-fr"


def test_ws21_9_rate_limit_event_is_supported():

    service = OperationalEventService()

    incident = service.record_event(
        make_event(
            event_type=(
                OperationalEventType.RATE_LIMIT
            ),
            severity=(
                OperationalSeverity.MEDIUM
            ),
        )
    )

    assert (
        incident.event_type
        is OperationalEventType.RATE_LIMIT
    )


def test_ws21_9_abuse_event_is_supported():

    service = OperationalEventService()

    incident = service.record_event(
        make_event(
            event_type=(
                OperationalEventType.ABUSE
            ),
            severity=(
                OperationalSeverity.HIGH
            ),
        )
    )

    assert (
        incident.event_type
        is OperationalEventType.ABUSE
    )


def test_ws21_9_dependency_failure_is_supported():

    service = OperationalEventService()

    incident = service.record_event(
        make_event(
            event_type=(
                OperationalEventType.DATABASE_FAILURE
            ),
            severity=(
                OperationalSeverity.CRITICAL
            ),
        )
    )

    assert (
        incident.event_type
        is OperationalEventType.DATABASE_FAILURE
    )


def test_ws21_9_private_and_announcement_are_separate():

    service = OperationalEventService()

    private = service.record_event(
        make_event(
            correlation_id="private-001",
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
        )
    )

    announcement = service.record_event(
        make_event(
            correlation_id="announcement-001",
            surface=(
                OperationalSurface.ANNOUNCEMENT_GROUP
            ),
            event_type=(
                OperationalEventType.NOTIFICATION_FAILURE
            ),
        )
    )

    assert (
        private.surface
        is OperationalSurface.PRIVATE_CLASSROOM
    )

    assert (
        announcement.surface
        is OperationalSurface.ANNOUNCEMENT_GROUP
    )

    private_incidents = (
        service.list_incidents(
            surface=OperationalSurface.PRIVATE_CLASSROOM
        )
    )

    announcement_incidents = (
        service.list_incidents(
            surface=OperationalSurface.ANNOUNCEMENT_GROUP
        )
    )

    assert len(private_incidents) == 1
    assert len(announcement_incidents) == 1


def test_ws21_9_incident_lifecycle():

    service = OperationalEventService()

    incident = service.record_event(
        make_event()
    )

    assert (
        incident.status
        is IncidentStatus.DETECTED
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.OPEN,
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.ACKNOWLEDGED,
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.INVESTIGATING,
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.RESOLVED,
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.CLOSED,
    )

    assert (
        incident.status
        is IncidentStatus.CLOSED
    )


def test_ws21_9_invalid_lifecycle_transition_is_rejected():

    service = OperationalEventService()

    incident = service.record_event(
        make_event()
    )

    with pytest.raises(
        ValueError,
        match="Invalid incident transition",
    ):
        service.transition_incident(
            incident_id=incident.incident_id,
            status=IncidentStatus.CLOSED,
        )


def test_ws21_9_unknown_incident_is_rejected():

    service = OperationalEventService()

    with pytest.raises(
        KeyError,
        match="Unknown incident",
    ):
        service.transition_incident(
            incident_id="does-not-exist",
            status=IncidentStatus.OPEN,
        )


def test_ws21_9_dashboard_snapshot_contains_kpis():

    service = OperationalEventService()

    service.record_event(
        make_event(
            correlation_id="critical-001",
            severity=(
                OperationalSeverity.CRITICAL
            ),
        )
    )

    service.record_event(
        make_event(
            correlation_id="medium-001",
            severity=(
                OperationalSeverity.MEDIUM
            ),
        )
    )

    snapshot = (
        service.dashboard_snapshot()
    )

    assert snapshot[
        "total_incidents"
    ] == 2

    assert snapshot[
        "open_incidents"
    ] == 2

    assert snapshot[
        "critical_incidents"
    ] == 1

    assert snapshot[
        "private_classroom_incidents"
    ] == 2


def test_ws21_9_sensitive_content_is_not_part_of_event_contract():

    event = make_event()

    payload = event.as_dict()

    assert "message" not in payload
    assert "prompt" not in payload
    assert "response" not in payload
    assert "password" not in payload
    assert "api_key" not in payload


def test_ws21_9_event_requires_correlation_id():

    with pytest.raises(
        ValueError,
        match="correlation_id cannot be empty",
    ):
        OperationalEvent(
            event_type=(
                OperationalEventType.MESSAGE_FAILURE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="   ",
        )


def test_ws21_9_event_identifiers_are_normalized():

    event = make_event(
        correlation_id="  corr-123\r\n"
    )

    assert (
        event.correlation_id
        == "corr-123"
    )


def test_ws21_9_open_incident_count():

    service = OperationalEventService()

    incident = service.record_event(
        make_event()
    )

    assert (
        service.count_open_incidents()
        == 1
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.OPEN,
    )

    service.transition_incident(
        incident_id=incident.incident_id,
        status=IncidentStatus.RESOLVED,
    )

    assert (
        service.count_open_incidents()
        == 0
    )