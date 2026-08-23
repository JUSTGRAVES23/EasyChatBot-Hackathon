"""
AI Service Provider Manager escalation service tests.

Validates:

Provider Intelligence
        |
        v
EscalationService
        |
        v
EscalationRepository
        |
        v
ProviderEscalation


The escalation service does not:

- send emails;
- change provider routing;
- execute providers;
- modify Runtime configuration.
"""

import pytest

from app.application.provider_management.escalation_repository import (
    InMemoryEscalationRepository,
)

from app.application.provider_management.escalation_service import (
    EscalationService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationStatus,
    EscalationType,
)


def create_service() -> EscalationService:
    """
    Create an escalation service using
    the in-memory repository.
    """

    repository = (
        InMemoryEscalationRepository()
    )

    return EscalationService(
        repository=repository,
    )


def test_create_escalation_persists_record() -> None:
    """
    Validate escalation creation and persistence.
    """

    repository = (
        InMemoryEscalationRepository()
    )

    service = EscalationService(
        repository=repository,
    )

    escalation = service.create_escalation(
        escalation_type=(
            EscalationType.LATENCY_DEGRADATION
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="openai",
        capability="conversation",
        message=(
            "GPT-5-mini latency increased "
            "significantly."
        ),
        recommendation=(
            "Review alternative providers "
            "for conversation workloads."
        ),
    )

    assert escalation.escalation_id

    assert (
        escalation.escalation_type
        == EscalationType.LATENCY_DEGRADATION
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

    assert escalation.recommendation == (
        "Review alternative providers "
        "for conversation workloads."
    )

    assert (
        escalation.status
        == EscalationStatus.OPEN
    )

    stored = repository.get_by_id(
        escalation.escalation_id
    )

    assert stored == escalation


def test_list_escalations_returns_history() -> None:
    """
    Validate escalation history retrieval.
    """

    repository = (
        InMemoryEscalationRepository()
    )

    service = EscalationService(
        repository=repository,
    )

    first = service.create_escalation(
        escalation_type=(
            EscalationType.COST_SPIKE
        ),
        severity=(
            EscalationSeverity.MEDIUM
        ),
        provider="openai",
        capability="research",
        message=(
            "Provider cost increased."
        ),
    )

    second = service.create_escalation(
        escalation_type=(
            EscalationType.PROVIDER_FAILURE
        ),
        severity=(
            EscalationSeverity.CRITICAL
        ),
        provider="ollama",
        capability="conversation",
        message=(
            "Provider execution failed."
        ),
    )

    history = service.list_escalations()

    assert len(history) == 2

    assert history[0] == first

    assert history[1] == second


def test_empty_provider_is_rejected() -> None:
    """
    Validate provider input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Provider cannot be empty.",
    ):
        service.create_escalation(
            escalation_type=(
                EscalationType.COST_SPIKE
            ),
            severity=(
                EscalationSeverity.LOW
            ),
            provider="",
            capability="research",
            message="Cost increased.",
        )


def test_empty_capability_is_rejected() -> None:
    """
    Validate capability input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Capability cannot be empty.",
    ):
        service.create_escalation(
            escalation_type=(
                EscalationType.QUALITY_DROP
            ),
            severity=(
                EscalationSeverity.MEDIUM
            ),
            provider="openai",
            capability="",
            message="Quality decreased.",
        )


def test_empty_message_is_rejected() -> None:
    """
    Validate escalation message input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Escalation message cannot be empty.",
    ):
        service.create_escalation(
            escalation_type=(
                EscalationType.PROVIDER_FAILURE
            ),
            severity=(
                EscalationSeverity.HIGH
            ),
            provider="gemini",
            capability="research",
            message="",
        )