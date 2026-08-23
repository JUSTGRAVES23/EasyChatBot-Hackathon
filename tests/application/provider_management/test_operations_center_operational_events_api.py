"""
EasyChatBot AI Operations Center operational events API tests.

Validates the read-only application boundary for operational
event history.

The API must:
- require OperationalEventService;
- retrieve events through the application service;
- serialize OperationalEvent objects into stable dictionaries;
- serialize UUIDs and datetimes safely;
- serialize enum values as strings;
- preserve structured metadata;
- preserve event ordering;
- remain read-only.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.application.provider_management.operational_event import (
    OperationalEvent,
    OperationalEventSeverity,
    OperationalEventType,
)
from app.application.provider_management.operational_event_service import (
    OperationalEventService,
)
from app.application.provider_management.operations_center_operational_events_api import (
    OperationsCenterOperationalEventsAPI,
)


def create_event(
    *,
    event_type: OperationalEventType = (
        OperationalEventType.PROVIDER_HEALTH_CHANGED
    ),
    severity: OperationalEventSeverity = (
        OperationalEventSeverity.INFO
    ),
    minute: int = 0,
    provider: str = "openai",
    correlation_id: str | None = "incident-001",
) -> OperationalEvent:
    """Create deterministic operational event data."""

    return OperationalEvent.create(
        event_type=event_type,
        severity=severity,
        source="provider_management",
        component="ProviderIncidentService",
        occurred_at=datetime(
            2026, 8, 15, 14, minute, tzinfo=timezone.utc
        ),
        message="Operational event test.",
        correlation_id=correlation_id,
        metadata={
            "provider": provider,
            "environment": "test",
        },
    )


def create_service_mock(
    events: tuple[OperationalEvent, ...],
) -> Mock:
    """Create a controlled OperationalEventService test double."""

    service = Mock(spec=OperationalEventService)
    service.list_events.return_value = events
    return service


def test_api_requires_operational_event_service() -> None:
    """Validate the dependency boundary."""

    with pytest.raises(
        ValueError,
        match="Operational event service cannot be None.",
    ):
        OperationsCenterOperationalEventsAPI(
            operational_event_service=None,  # type: ignore[arg-type]
        )


def test_list_events_delegates_to_operational_event_service() -> None:
    """Validate event retrieval delegation."""

    event = create_event()
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    api.list_events()

    service.list_events.assert_called_once_with()


def test_list_events_returns_empty_list_when_no_events_exist() -> None:
    """Validate empty operational-event history."""

    service = create_service_mock(())

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    assert api.list_events() == []


def test_list_events_serializes_event_identity() -> None:
    """Validate UUID serialization."""

    event = create_event()
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert result[0]["event_id"] == str(event.event_id)
    assert isinstance(result[0]["event_id"], str)


def test_list_events_serializes_enum_values() -> None:
    """Validate event type and severity serialization."""

    event = create_event(
        event_type=OperationalEventType.PROVIDER_INCIDENT_CREATED,
        severity=OperationalEventSeverity.CRITICAL,
    )
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert result[0]["event_type"] == "provider_incident_created"
    assert result[0]["severity"] == "critical"
    assert isinstance(result[0]["event_type"], str)
    assert isinstance(result[0]["severity"], str)


def test_list_events_serializes_datetime() -> None:
    """Validate timezone-aware timestamp serialization."""

    event = create_event(minute=7)
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert result[0]["occurred_at"] == event.occurred_at.isoformat()
    assert isinstance(result[0]["occurred_at"], str)


def test_list_events_preserves_event_fields() -> None:
    """Validate the stable presentation contract."""

    event = create_event(
        provider="gemini",
        correlation_id="incident-002",
    )
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert result[0] == {
        "event_id": str(event.event_id),
        "event_type": event.event_type.value,
        "severity": event.severity.value,
        "source": event.source,
        "component": event.component,
        "occurred_at": event.occurred_at.isoformat(),
        "message": event.message,
        "correlation_id": event.correlation_id,
        "metadata": {
            "provider": "gemini",
            "environment": "test",
        },
    }


def test_list_events_preserves_event_order() -> None:
    """Validate that API serialization does not reorder events."""

    first = create_event(minute=1)
    second = create_event(
        event_type=OperationalEventType.PROVIDER_INCIDENT_CREATED,
        severity=OperationalEventSeverity.CRITICAL,
        minute=2,
    )
    third = create_event(
        event_type=OperationalEventType.PROVIDER_RECOVERED,
        minute=3,
    )

    service = create_service_mock((first, second, third))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert [item["event_id"] for item in result] == [
        str(first.event_id),
        str(second.event_id),
        str(third.event_id),
    ]


def test_list_events_preserves_structured_metadata() -> None:
    """Validate structured operational-event metadata."""

    event = OperationalEvent.create(
        event_type=OperationalEventType.PROVIDER_INCIDENT_CREATED,
        severity=OperationalEventSeverity.CRITICAL,
        source="provider_management",
        component="ProviderIncidentService",
        occurred_at=datetime(
            2026, 8, 15, 14, 5, tzinfo=timezone.utc
        ),
        message="Provider incident created.",
        correlation_id="incident-005",
        metadata={
            "provider": "openai",
            "incident_id": "incident-005",
            "consecutive_failures": 3,
            "affected_capabilities": [
                "conversation",
                "reasoning",
            ],
        },
    )

    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert result[0]["metadata"] == {
        "provider": "openai",
        "incident_id": "incident-005",
        "consecutive_failures": 3,
        "affected_capabilities": [
            "conversation",
            "reasoning",
        ],
    }


def test_list_events_preserves_null_correlation_id() -> None:
    """Validate events without correlation IDs."""

    event = create_event(correlation_id=None)
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert result[0]["correlation_id"] is None


def test_api_does_not_write_events() -> None:
    """Validate the read-only API surface."""

    event = create_event()
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    api.list_events()

    service.list_events.assert_called_once_with()

    assert not hasattr(api, "record")
    assert not hasattr(api, "create")
    assert not hasattr(api, "delete")


def test_serialized_event_is_json_safe() -> None:
    """Validate that the response contains JSON-safe values."""

    event = create_event(
        event_type=OperationalEventType.AGENT_EXECUTION_FAILED,
        severity=OperationalEventSeverity.ERROR,
    )
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    def assert_json_safe(value: object) -> None:
        if value is None:
            return

        if isinstance(value, (str, int, float, bool)):
            return

        if isinstance(value, list):
            for item in value:
                assert_json_safe(item)
            return

        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                assert_json_safe(item)
            return

        raise AssertionError(
            "Response contains a non-JSON-safe "
            f"value: {type(value)!r}"
        )

    assert_json_safe(result)


def test_serialized_event_does_not_expose_internal_objects() -> None:
    """Validate that UUIDs and enums do not cross the API boundary."""

    event = create_event()
    service = create_service_mock((event,))

    api = OperationsCenterOperationalEventsAPI(
        operational_event_service=service,
    )

    result = api.list_events()

    assert isinstance(result[0]["event_id"], str)
    assert isinstance(result[0]["event_type"], str)
    assert isinstance(result[0]["severity"], str)
    assert not isinstance(
        result[0]["event_type"],
        OperationalEventType,
    )
    assert not isinstance(
        result[0]["severity"],
        OperationalEventSeverity,
    )