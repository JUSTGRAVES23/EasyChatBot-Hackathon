"""
EasyChatBot AI Operations Center provider operational event tests.

Validates the provider-specific adapter between:

Provider Incident
        |
        v
ProviderOperationalEventService
        |
        v
OperationalEventService
        |
        v
OperationalEvent

The adapter must:

- create PROVIDER_INCIDENT_CREATED events;
- create PROVIDER_RECOVERED events;
- preserve incident correlation;
- preserve provider metadata;
- delegate persistence to OperationalEventService;
- reject invalid input;
- remain read-only with respect to provider state.
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

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
    ProviderIncident,
)

from app.application.provider_management.provider_operational_event_service import (
    ProviderOperationalEventService,
)


def create_incident(
    *,
    incident_id: str = "incident-001",
    provider: str = "openai",
    status: ProviderHealthStatus = (
        ProviderHealthStatus.UNAVAILABLE
    ),
    started_at: datetime | None = None,
    recovered_at: datetime | None = None,
    capabilities: tuple[str, ...] = (
        "conversation",
    ),
    consecutive_failures: int = 3,
) -> ProviderIncident:
    """
    Create deterministic provider incident data.
    """

    if started_at is None:
        started_at = datetime(
            2026,
            8,
            15,
            14,
            0,
            tzinfo=timezone.utc,
        )

    return ProviderIncident(
        incident_id=incident_id,
        provider=provider,
        status=status,
        started_at=started_at,
        last_observed_at=(
            recovered_at
            if recovered_at is not None
            else started_at
        ),
        recovered_at=recovered_at,
        affected_capabilities=capabilities,
        consecutive_failures=consecutive_failures,
        resolution_message=(
            "Provider recovered."
            if recovered_at is not None
            else None
        ),
    )


def create_service() -> tuple[
    ProviderOperationalEventService,
    Mock,
]:
    """
    Create the provider operational event adapter with a
    controlled generic operational event service.
    """

    operational_event_service = Mock(
        spec=OperationalEventService,
    )

    operational_event_service.record.side_effect = (
        lambda event: event
    )

    service = ProviderOperationalEventService(
        operational_event_service=(
            operational_event_service
        )
    )

    return (
        service,
        operational_event_service,
    )


def test_incident_created_creates_operational_event() -> None:
    """
    Validate provider incident creation mapping.
    """

    service, _ = create_service()

    incident = create_incident()

    result = service.record_incident_created(
        incident=incident,
    )

    assert isinstance(
        result,
        OperationalEvent,
    )

    assert (
        result.event_type
        == OperationalEventType.PROVIDER_INCIDENT_CREATED
    )

    assert (
        result.severity
        == OperationalEventSeverity.CRITICAL
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
        result.occurred_at
        == incident.started_at
    )

    assert (
        result.correlation_id
        == incident.incident_id
    )


def test_incident_created_preserves_provider_metadata() -> None:
    """
    Validate provider incident context in structured metadata.
    """

    service, _ = create_service()

    incident = create_incident(
        provider="gemini",
        incident_id="incident-002",
        capabilities=(
            "summarisation",
            "reasoning",
        ),
        consecutive_failures=5,
    )

    result = service.record_incident_created(
        incident=incident,
    )

    assert (
        result.metadata["provider"]
        == "gemini"
    )

    assert (
        result.metadata["incident_id"]
        == "incident-002"
    )

    assert (
        result.metadata["status"]
        == ProviderHealthStatus.UNAVAILABLE.value
    )

    assert (
        result.metadata["affected_capabilities"]
        == [
            "summarisation",
            "reasoning",
        ]
    )

    assert (
        result.metadata["consecutive_failures"]
        == 5
    )


def test_incident_created_is_persisted_through_generic_service() -> None:
    """
    Validate delegation to the generic operational event service.
    """

    service, operational_events = create_service()

    incident = create_incident()

    result = service.record_incident_created(
        incident=incident,
    )

    operational_events.record.assert_called_once_with(
        result
    )


def test_provider_recovered_creates_operational_event() -> None:
    """
    Validate provider recovery mapping.
    """

    service, _ = create_service()

    recovered_at = datetime(
        2026,
        8,
        15,
        14,
        7,
        tzinfo=timezone.utc,
    )

    incident = create_incident(
        status=ProviderHealthStatus.HEALTHY,
        recovered_at=recovered_at,
    )

    result = service.record_provider_recovered(
        incident=incident,
    )

    assert isinstance(
        result,
        OperationalEvent,
    )

    assert (
        result.event_type
        == OperationalEventType.PROVIDER_RECOVERED
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
        result.occurred_at
        == recovered_at
    )

    assert (
        result.correlation_id
        == incident.incident_id
    )


def test_provider_recovered_preserves_recovery_metadata() -> None:
    """
    Validate recovery metadata.
    """

    service, _ = create_service()

    recovered_at = datetime(
        2026,
        8,
        15,
        14,
        7,
        tzinfo=timezone.utc,
    )

    incident = create_incident(
        provider="gemini",
        incident_id="incident-003",
        status=ProviderHealthStatus.HEALTHY,
        recovered_at=recovered_at,
    )

    result = service.record_provider_recovered(
        incident=incident,
    )

    assert (
        result.metadata["provider"]
        == "gemini"
    )

    assert (
        result.metadata["incident_id"]
        == "incident-003"
    )

    assert (
        result.metadata["status"]
        == ProviderHealthStatus.HEALTHY.value
    )

    assert (
        result.metadata["affected_capabilities"]
        == ["conversation"]
    )


def test_provider_recovered_requires_recovery_timestamp() -> None:
    """
    Validate recovery timestamp requirement.
    """

    service, _ = create_service()

    incident = create_incident()

    with pytest.raises(
        ValueError,
        match=(
            "Recovered provider incident must "
            "have a recovery timestamp."
        ),
    ):
        service.record_provider_recovered(
            incident=incident,
        )


def test_none_incident_is_rejected_for_creation() -> None:
    """
    Validate required incident input.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Provider incident cannot be None.",
    ):
        service.record_incident_created(
            incident=None,  # type: ignore[arg-type]
        )


def test_none_incident_is_rejected_for_recovery() -> None:
    """
    Validate required incident input for recovery.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Provider incident cannot be None.",
    ):
        service.record_provider_recovered(
            incident=None,  # type: ignore[arg-type]
        )


def test_adapter_does_not_execute_provider_operations() -> None:
    """
    Validate that the adapter only records an operational fact.

    It must not expose or invoke provider execution behaviour.
    """

    service, operational_events = create_service()

    incident = create_incident()

    result = service.record_incident_created(
        incident=incident,
    )

    assert result is not None

    operational_events.record.assert_called_once_with(
        result
    )