"""
EasyChatBot AI Operations Center escalation detail tests.

Validates:

Escalation Repository
        |
        v
EscalationDetailService
        |
        v
EscalationDetail
        |
        v
AI Operations Center

The detail service is read-only.

It does not:

- modify escalations;
- resolve escalations;
- approve recommendations;
- send emails;
- change provider routing.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.escalation_detail_service import (
    EscalationDetailService,
)

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


def create_escalation_service() -> tuple[
    EscalationService,
    InMemoryEscalationRepository,
]:
    """
    Create an escalation service with an in-memory repository.
    """

    repository = (
        InMemoryEscalationRepository()
    )

    service = EscalationService(
        repository=repository,
    )

    return service, repository


def test_get_detail_returns_escalation_information() -> None:
    """
    Validate retrieval of a complete escalation detail.
    """

    escalation_service, repository = (
        create_escalation_service()
    )

    escalation = (
        escalation_service.create_escalation(
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
    )

    detail_service = (
        EscalationDetailService(
            repository=repository,
        )
    )

    detail = (
        detail_service.get_detail(
            escalation.escalation_id
        )
    )

    assert detail is not None

    assert (
        detail.escalation_id
        == escalation.escalation_id
    )

    assert (
        detail.escalation_type
        == EscalationType.LATENCY_DEGRADATION
    )

    assert (
        detail.severity
        == EscalationSeverity.HIGH
    )

    assert detail.provider == "openai"

    assert (
        detail.capability
        == "conversation"
    )

    assert (
        detail.message
        == (
            "GPT-5-mini latency increased "
            "significantly."
        )
    )

    assert (
        detail.recommendation
        == (
            "Review alternative providers "
            "for conversation workloads."
        )
    )

    assert (
        detail.status
        == EscalationStatus.OPEN
    )


def test_get_detail_preserves_created_at() -> None:
    """
    Validate preservation of the escalation timestamp.
    """

    escalation_service, repository = (
        create_escalation_service()
    )

    escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.COST_SPIKE
            ),
            severity=(
                EscalationSeverity.MEDIUM
            ),
            provider="gemini",
            capability="summarisation",
            message=(
                "Provider cost increased."
            ),
        )
    )

    detail_service = (
        EscalationDetailService(
            repository=repository,
        )
    )

    detail = (
        detail_service.get_detail(
            escalation.escalation_id
        )
    )

    assert detail is not None

    assert (
        detail.created_at
        == escalation.created_at
    )

    assert (
        detail.created_at.tzinfo
        == timezone.utc
    )


def test_missing_escalation_returns_none() -> None:
    """
    Validate behaviour when an escalation does not exist.
    """

    _, repository = (
        create_escalation_service()
    )

    detail_service = (
        EscalationDetailService(
            repository=repository,
        )
    )

    detail = (
        detail_service.get_detail(
            "does-not-exist"
        )
    )

    assert detail is None


def test_empty_escalation_id_is_rejected() -> None:
    """
    Validate escalation identifier input.
    """

    _, repository = (
        create_escalation_service()
    )

    detail_service = (
        EscalationDetailService(
            repository=repository,
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Escalation id cannot be empty."
        ),
    ):
        detail_service.get_detail("")


def test_detail_service_is_read_only() -> None:
    """
    Validate that reading escalation details does not
    remove or modify the repository record.
    """

    escalation_service, repository = (
        create_escalation_service()
    )

    escalation = (
        escalation_service.create_escalation(
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
            recommendation=(
                "Review provider availability."
            ),
        )
    )

    detail_service = (
        EscalationDetailService(
            repository=repository,
        )
    )

    detail_service.get_detail(
        escalation.escalation_id
    )

    stored = repository.get_by_id(
        escalation.escalation_id
    )

    assert stored is not None

    assert (
        stored.escalation_id
        == escalation.escalation_id
    )

    assert (
        stored.status
        == EscalationStatus.OPEN
    )