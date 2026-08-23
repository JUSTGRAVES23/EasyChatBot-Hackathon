"""
EasyChatBot AI Operations Center provider health escalation tests.

Validates:

Provider Health
        |
        v
Provider Incident
        |
        v
Health Escalation Service
        |
        v
Escalation Service
        |
        v
Provider Escalation

The tests verify that provider availability incidents
are translated into advisory operational escalations.

No email, Runtime routing change, provider execution,
or autonomous action is performed.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.application.provider_management.escalation_repository import (
    EscalationRepository,
    InMemoryEscalationRepository,
)

from app.application.provider_management.escalation_service import (
    EscalationService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationType,
)

from app.application.provider_management.provider_health_escalation_service import (
    ProviderHealthEscalationService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
    ProviderIncident,
)


def create_incident(
    *,
    provider: str = "openai",
    status: ProviderHealthStatus = (
        ProviderHealthStatus.UNAVAILABLE
    ),
    consecutive_failures: int = 3,
    capabilities: tuple[str, ...] = (
        "conversation",
    ),
) -> ProviderIncident:
    """
    Create a deterministic provider incident.
    """

    started_at = datetime(
        2026,
        8,
        14,
        14,
        32,
        tzinfo=timezone.utc,
    )

    observed_at = datetime(
        2026,
        8,
        14,
        14,
        35,
        tzinfo=timezone.utc,
    )

    return ProviderIncident(
        incident_id="incident-001",
        provider=provider,
        status=status,
        started_at=started_at,
        last_observed_at=observed_at,
        recovered_at=None,
        affected_capabilities=capabilities,
        consecutive_failures=consecutive_failures,
        resolution_message=None,
    )


def create_service() -> (
    ProviderHealthEscalationService
):
    """
    Create the health escalation service with an
    in-memory escalation repository.
    """

    repository = (
        InMemoryEscalationRepository()
    )

    escalation_service = (
        EscalationService(
            repository=repository
        )
    )

    return ProviderHealthEscalationService(
        escalation_service=escalation_service
    )


def test_unavailable_provider_creates_escalation() -> None:
    """
    Validate that an unavailable provider creates a
    provider failure escalation.
    """

    service = create_service()

    incident = create_incident(
        provider="openai",
        consecutive_failures=3,
        capabilities=(
            "conversation",
        ),
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is not None

    assert (
        escalation.escalation_type
        == EscalationType.PROVIDER_FAILURE
    )

    assert (
        escalation.severity
        == EscalationSeverity.HIGH
    )

    assert escalation.provider == "openai"

    assert (
        escalation.capability
        == "conversation"
    )

    assert (
        "currently unavailable"
        in escalation.message
    )

    assert (
        "3"
        in escalation.message
    )

    assert (
        escalation.recommendation
        is not None
    )


def test_multiple_capabilities_are_preserved() -> None:
    """
    Validate that all affected capabilities are included
    in the escalation scope.
    """

    service = create_service()

    incident = create_incident(
        provider="openai",
        capabilities=(
            "conversation",
            "summarisation",
        ),
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is not None

    assert (
        escalation.capability
        == "conversation, summarisation"
    )

    assert (
        "conversation, summarisation"
        in escalation.message
    )


def test_five_failures_create_critical_escalation() -> None:
    """
    Validate the Hackathon severity threshold.

    Five or more consecutive failures produce a
    critical provider failure escalation.
    """

    service = create_service()

    incident = create_incident(
        provider="gemini",
        consecutive_failures=5,
        capabilities=(
            "summarisation",
        ),
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is not None

    assert (
        escalation.severity
        == EscalationSeverity.CRITICAL
    )

    assert (
        escalation.escalation_type
        == EscalationType.PROVIDER_FAILURE
    )


def test_recovered_incident_does_not_create_active_escalation() -> None:
    """
    Validate that an already recovered incident does not
    create an active provider failure escalation.
    """

    service = create_service()

    incident = create_incident(
        provider="openai",
        status=ProviderHealthStatus.HEALTHY,
        consecutive_failures=3,
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is None


def test_none_incident_is_rejected() -> None:
    """
    Validate required incident input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Provider incident cannot be None.",
    ):
        service.escalate_incident(
            incident=None,  # type: ignore[arg-type]
        )


def test_empty_provider_is_rejected() -> None:
    """
    Validate provider identity.
    """

    service = create_service()

    incident = create_incident(
        provider="   "
    )

    with pytest.raises(
        ValueError,
        match="Provider cannot be empty.",
    ):
        service.escalate_incident(
            incident=incident
        )


def test_escalation_recommendation_is_advisory() -> None:
    """
    Validate that the generated recommendation explicitly
    preserves human approval.

    The health escalation service must not instruct the
    system to autonomously change Runtime routing.
    """

    service = create_service()

    incident = create_incident(
        provider="openai",
        consecutive_failures=3,
        capabilities=(
            "conversation",
        ),
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is not None

    assert (
        escalation.recommendation
        is not None
    )

    assert (
        "human"
        in escalation.recommendation.lower()
    )

    assert (
        "approval"
        in escalation.recommendation.lower()
    )


def test_provider_failure_escalation_contains_incident_timing() -> None:
    """
    Validate that the escalation message contains the
    incident start timestamp.

    This allows the Operations Center to explain when
    the provider failure began.
    """

    service = create_service()

    incident = create_incident(
        provider="openai",
        consecutive_failures=3,
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is not None

    assert (
        incident.started_at.isoformat()
        in escalation.message
    )


def test_escalation_is_persisted_by_escalation_service() -> None:
    """
    Validate the complete persistence boundary.

    Health escalation service
        ->
    EscalationService
        ->
    EscalationRepository
    """

    repository = (
        InMemoryEscalationRepository()
    )

    escalation_service = (
        EscalationService(
            repository=repository
        )
    )

    service = (
        ProviderHealthEscalationService(
            escalation_service=escalation_service
        )
    )

    incident = create_incident(
        provider="ollama",
        consecutive_failures=3,
        capabilities=(
            "internal_experiments",
        ),
    )

    escalation = service.escalate_incident(
        incident=incident
    )

    assert escalation is not None

    persisted = (
        escalation_service
        .list_escalations()
    )

    assert len(persisted) == 1

    assert (
        persisted[0].escalation_id
        == escalation.escalation_id
    )

    assert (
        persisted[0].provider
        == "ollama"
    )

    assert (
        persisted[0].escalation_type
        == EscalationType.PROVIDER_FAILURE
    )