"""
EasyChatBot AI Operations Center operational events API
integration tests.

Validates the real application path:

OperationalEventRepository
        |
        v
OperationalEventService
        |
        v
OperationsCenterOperationalEventsAPI

This test deliberately uses the real in-memory repository and
real OperationalEventService.

It does not call:

- external providers;
- external APIs;
- Runtime routing;
- autonomous operational actions.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.provider_management.operational_event import (
    OperationalEvent,
    OperationalEventSeverity,
    OperationalEventType,
)

from app.application.provider_management.operational_event_repository import (
    InMemoryOperationalEventRepository,
)

from app.application.provider_management.operational_event_service import (
    OperationalEventService,
)

from app.application.provider_management.operations_center_operational_events_api import (
    OperationsCenterOperationalEventsAPI,
)


def create_service() -> OperationalEventService:
    """
    Create the real operational event application service
    with an isolated in-memory repository.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    return OperationalEventService(
        repository=repository,
    )


def create_event(
    *,
    minute: int,
    event_type: OperationalEventType,
    severity: OperationalEventSeverity,
) -> OperationalEvent:
    """
    Create deterministic operational event data.
    """

    return OperationalEvent.create(
        event_type=event_type,
        severity=severity,
        source="provider_management",
        component="ProviderIncidentService",
        occurred_at=datetime(
            2026,
            8,
            15,
            14,
            minute,
            tzinfo=timezone.utc,
        ),
        message="Operational event integration test.",
        correlation_id="integration-001",
        metadata={
            "provider": "openai",
            "environment": "test",
        },
    )


def test_api_reads_events_from_real_operational_event_service() -> None:
    """
    Validate the complete API read path using the real
    OperationalEventService.
    """

    service = create_service()

    event = create_event(
        minute=1,
        event_type=(
            OperationalEventType
            .PROVIDER_INCIDENT_CREATED
        ),
        severity=(
            OperationalEventSeverity.CRITICAL
        ),
    )

    service.record(event)

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert len(result) == 1

    assert (
        result[0]["event_id"]
        == str(event.event_id)
    )

    assert (
        result[0]["event_type"]
        == "provider_incident_created"
    )

    assert (
        result[0]["severity"]
        == "critical"
    )

    assert (
        result[0]["source"]
        == "provider_management"
    )

    assert (
        result[0]["component"]
        == "ProviderIncidentService"
    )

    assert (
        result[0]["correlation_id"]
        == "integration-001"
    )

    assert (
        result[0]["metadata"]["provider"]
        == "openai"
    )


def test_api_reads_multiple_events_in_repository_order() -> None:
    """
    Validate multiple operational facts through the real
    application service.
    """

    service = create_service()

    first = create_event(
        minute=1,
        event_type=(
            OperationalEventType
            .PROVIDER_INCIDENT_CREATED
        ),
        severity=(
            OperationalEventSeverity.CRITICAL
        ),
    )

    second = create_event(
        minute=2,
        event_type=(
            OperationalEventType
            .PROVIDER_RECOVERED
        ),
        severity=(
            OperationalEventSeverity.INFO
        ),
    )

    service.record(first)
    service.record(second)

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert [
        item["event_id"]
        for item in result
    ] == [
        str(first.event_id),
        str(second.event_id),
    ]

    assert [
        item["event_type"]
        for item in result
    ] == [
        "provider_incident_created",
        "provider_recovered",
    ]


def test_api_returns_empty_history_from_new_service() -> None:
    """
    Validate that a fresh composition exposes no fabricated
    operational events.
    """

    service = create_service()

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    assert api.list_events() == []


def test_api_reflects_events_recorded_after_api_creation() -> None:
    """
    Validate that the API reads current service state rather
    than taking a snapshot during construction.
    """

    service = create_service()

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    assert api.list_events() == []

    event = create_event(
        minute=3,
        event_type=(
            OperationalEventType
            .AGENT_EXECUTION_COMPLETED
        ),
        severity=(
            OperationalEventSeverity.INFO
        ),
    )

    service.record(event)

    result = api.list_events()

    assert len(result) == 1

    assert (
        result[0]["event_id"]
        == str(event.event_id)
    )