"""
EasyChatBot AI Operations Center operational event service tests.

Validates the generic application boundary:

OperationalEvent
        |
        v
OperationalEventService
        |
        v
OperationalEventRepository

The service must:

- reject invalid dependencies;
- reject invalid events;
- persist immutable operational facts through
  the repository abstraction;
- retrieve events by ID;
- return events in repository order;
- expose an isolated clear operation.

The service must NOT:

- know about providers;
- know about incidents;
- execute Runtime operations;
- execute agents;
- perform autonomous actions;
- access persistence infrastructure directly.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest

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


def create_event(
    *,
    event_type: OperationalEventType = (
        OperationalEventType.PROVIDER_HEALTH_CHANGED
    ),
    severity: OperationalEventSeverity = (
        OperationalEventSeverity.INFO
    ),
    source: str = "test",
    component: str = "test_component",
    minute: int = 0,
    correlation_id: str | None = "correlation-001",
    metadata: dict[str, object] | None = None,
) -> OperationalEvent:
    """
    Create a deterministic operational event.
    """

    return OperationalEvent.create(
        event_type=event_type,
        severity=severity,
        source=source,
        component=component,
        occurred_at=datetime(
            2026,
            8,
            15,
            14,
            minute,
            tzinfo=timezone.utc,
        ),
        message="Operational event test.",
        correlation_id=correlation_id,
        metadata=(
            metadata
            if metadata is not None
            else {
                "test": True,
            }
        ),
    )


def create_service() -> (
    tuple[
        OperationalEventService,
        InMemoryOperationalEventRepository,
    ]
):
    """
    Create a service with an isolated in-memory repository.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    service = OperationalEventService(
        repository=repository,
    )

    return service, repository


def test_service_requires_repository() -> None:
    """
    Validate the composition dependency boundary.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operational event repository "
            "cannot be None."
        ),
    ):
        OperationalEventService(
            repository=None,  # type: ignore[arg-type]
        )


def test_record_rejects_none_event() -> None:
    """
    Validate required event input.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Operational event cannot be None.",
    ):
        service.record(
            None,  # type: ignore[arg-type]
        )


def test_record_persists_and_returns_same_event() -> None:
    """
    Validate immutable event persistence.

    The service must return the exact event supplied by
    the caller after successful persistence.
    """

    service, repository = create_service()

    event = create_event()

    result = service.record(event)

    assert result is event

    stored = repository.get_by_id(
        event.event_id
    )

    assert stored is event


def test_get_event_returns_persisted_event() -> None:
    """
    Validate retrieval by event ID.
    """

    service, _ = create_service()

    event = create_event()

    service.record(event)

    result = service.get_event(
        event.event_id
    )

    assert result is event


def test_get_event_returns_none_for_unknown_id() -> None:
    """
    Validate unknown event lookup.
    """

    service, _ = create_service()

    unknown_id = UUID(
        "00000000-0000-0000-0000-000000000001"
    )

    assert (
        service.get_event(
            unknown_id
        )
        is None
    )


def test_get_event_rejects_none_id() -> None:
    """
    Validate required event ID.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Operational event ID cannot be None."
        ),
    ):
        service.get_event(
            None,  # type: ignore[arg-type]
        )


def test_list_events_returns_repository_order() -> None:
    """
    Validate that the application service does not
    reorder repository results.
    """

    service, _ = create_service()

    first = create_event(
        minute=1,
    )

    second = create_event(
        event_type=(
            OperationalEventType
            .PROVIDER_INCIDENT_CREATED
        ),
        severity=(
            OperationalEventSeverity.CRITICAL
        ),
        minute=2,
    )

    third = create_event(
        event_type=(
            OperationalEventType
            .PROVIDER_RECOVERED
        ),
        minute=3,
    )

    service.record(first)
    service.record(second)
    service.record(third)

    events = service.list_events()

    assert events == (
        first,
        second,
        third,
    )


def test_list_events_is_empty_initially() -> None:
    """
    Validate isolated service state.
    """

    service, _ = create_service()

    assert service.list_events() == ()


def test_clear_removes_all_events() -> None:
    """
    Validate isolated state reset.
    """

    service, _ = create_service()

    first = create_event(
        minute=1,
    )

    second = create_event(
        minute=2,
    )

    service.record(first)
    service.record(second)

    assert len(
        service.list_events()
    ) == 2

    service.clear()

    assert service.list_events() == ()


def test_event_identity_and_metadata_are_preserved() -> None:
    """
    Validate that the generic service does not transform
    operational event content.
    """

    service, _ = create_service()

    event = create_event(
        source="provider_management",
        component="ProviderIncidentService",
        correlation_id="incident-001",
        metadata={
            "provider": "openai",
            "incident_id": "incident-001",
        },
    )

    result = service.record(event)

    assert result.event_id == event.event_id

    assert (
        result.event_type
        == OperationalEventType.PROVIDER_HEALTH_CHANGED
    )

    assert (
        result.severity
        == OperationalEventSeverity.INFO
    )

    assert (
        result.source
        == "provider_management"
    )

    assert (
        result.component
        == "ProviderIncidentService"
    )

    assert (
        result.correlation_id
        == "incident-001"
    )

    assert (
        result.metadata["provider"]
        == "openai"
    )


def test_service_remains_provider_agnostic() -> None:
    """
    Validate that the generic service can record different
    operational event categories without provider-specific
    branching.
    """

    service, _ = create_service()

    events = (
        create_event(
            event_type=(
                OperationalEventType
                .PROVIDER_HEALTH_CHANGED
            ),
        ),
        create_event(
            event_type=(
                OperationalEventType
                .PROVIDER_INCIDENT_CREATED
            ),
            severity=(
                OperationalEventSeverity.CRITICAL
            ),
            minute=1,
        ),
        create_event(
            event_type=(
                OperationalEventType
                .PROVIDER_RECOVERED
            ),
            minute=2,
        ),
        create_event(
            event_type=(
                OperationalEventType
                .AGENT_EXECUTION_FAILED
            ),
            severity=(
                OperationalEventSeverity.ERROR
            ),
            minute=3,
        ),
    )

    for event in events:
        service.record(event)

    result = service.list_events()

    assert result == events