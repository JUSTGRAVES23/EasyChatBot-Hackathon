"""
EasyChatBot AI Operations Center escalation type tests.

Validates:

Escalation Repository
        |
        v
EscalationTypeService
        |
        v
EscalationTypeSummary
        |
        v
AI Operations Center

The service is read-only.

It does not:

- create escalations;
- modify escalations;
- approve recommendations;
- send emails;
- change provider routing.
"""

from app.application.provider_management.escalation_repository import (
    InMemoryEscalationRepository,
)

from app.application.provider_management.escalation_service import (
    EscalationService,
)

from app.application.provider_management.escalation_type_service import (
    EscalationTypeService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationStatus,
    EscalationType,
)


def create_services() -> tuple[
    EscalationService,
    EscalationTypeService,
    InMemoryEscalationRepository,
]:
    """
    Create the escalation services and repository.
    """

    repository = (
        InMemoryEscalationRepository()
    )

    escalation_service = EscalationService(
        repository=repository,
    )

    type_service = EscalationTypeService(
        repository=repository,
    )

    return (
        escalation_service,
        type_service,
        repository,
    )


def test_summary_contains_all_escalation_types() -> None:
    """
    Validate that every supported escalation type
    is represented, including types with zero incidents.
    """

    (
        _,
        type_service,
        _,
    ) = create_services()

    summaries = (
        type_service.get_summary()
    )

    types = tuple(
        summary.escalation_type
        for summary in summaries
    )

    assert types == tuple(
        EscalationType
    )

    assert len(summaries) == len(
        EscalationType
    )


def test_summary_counts_escalations_by_type() -> None:
    """
    Validate aggregation of escalation counts.
    """

    (
        escalation_service,
        type_service,
        _,
    ) = create_services()

    escalation_service.create_escalation(
        escalation_type=(
            EscalationType.COST_SPIKE
        ),
        severity=(
            EscalationSeverity.MEDIUM
        ),
        provider="openai",
        capability="conversation",
        message="Cost increased.",
    )

    escalation_service.create_escalation(
        escalation_type=(
            EscalationType.COST_SPIKE
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="openai",
        capability="research",
        message="Research cost increased.",
    )

    escalation_service.create_escalation(
        escalation_type=(
            EscalationType.QUALITY_DROP
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="gemini",
        capability="summarisation",
        message="Quality decreased.",
    )

    summaries = (
        type_service.get_summary()
    )

    summary_by_type = {
        summary.escalation_type: summary
        for summary in summaries
    }

    assert (
        summary_by_type[
            EscalationType.COST_SPIKE
        ].total_count
        == 2
    )

    assert (
        summary_by_type[
            EscalationType.QUALITY_DROP
        ].total_count
        == 1
    )

    assert (
        summary_by_type[
            EscalationType.PROVIDER_FAILURE
        ].total_count
        == 0
    )

    assert (
        summary_by_type[
            EscalationType.LATENCY_DEGRADATION
        ].total_count
        == 0
    )


def test_summary_counts_only_open_and_acknowledged_as_active() -> None:
    """
    Validate that resolved and dismissed escalations
    are excluded from active counts.
    """

    (
        escalation_service,
        type_service,
        repository,
    ) = create_services()

    open_escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.PROVIDER_FAILURE
            ),
            severity=(
                EscalationSeverity.CRITICAL
            ),
            provider="ollama",
            capability="conversation",
            message="Provider unavailable.",
        )
    )

    acknowledged_escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.PROVIDER_FAILURE
            ),
            severity=(
                EscalationSeverity.HIGH
            ),
            provider="ollama",
            capability="research",
            message="Provider degraded.",
        )
    )

    resolved_escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.PROVIDER_FAILURE
            ),
            severity=(
                EscalationSeverity.HIGH
            ),
            provider="ollama",
            capability="conversation",
            message="Provider was unavailable.",
        )
    )

    dismissed_escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.PROVIDER_FAILURE
            ),
            severity=(
                EscalationSeverity.MEDIUM
            ),
            provider="ollama",
            capability="research",
            message="Transient provider issue.",
        )
    )

    repository.clear()

    repository.save(
        open_escalation
    )

    repository.save(
        acknowledged_escalation.__class__(
            escalation_id=(
                acknowledged_escalation.escalation_id
            ),
            escalation_type=(
                acknowledged_escalation.escalation_type
            ),
            severity=(
                acknowledged_escalation.severity
            ),
            provider=(
                acknowledged_escalation.provider
            ),
            capability=(
                acknowledged_escalation.capability
            ),
            message=(
                acknowledged_escalation.message
            ),
            recommendation=(
                acknowledged_escalation.recommendation
            ),
            created_at=(
                acknowledged_escalation.created_at
            ),
            status=(
                EscalationStatus.ACKNOWLEDGED
            ),
        )
    )

    repository.save(
        resolved_escalation.__class__(
            escalation_id=(
                resolved_escalation.escalation_id
            ),
            escalation_type=(
                resolved_escalation.escalation_type
            ),
            severity=(
                resolved_escalation.severity
            ),
            provider=(
                resolved_escalation.provider
            ),
            capability=(
                resolved_escalation.capability
            ),
            message=(
                resolved_escalation.message
            ),
            recommendation=(
                resolved_escalation.recommendation
            ),
            created_at=(
                resolved_escalation.created_at
            ),
            status=(
                EscalationStatus.RESOLVED
            ),
        )
    )

    repository.save(
        dismissed_escalation.__class__(
            escalation_id=(
                dismissed_escalation.escalation_id
            ),
            escalation_type=(
                dismissed_escalation.escalation_type
            ),
            severity=(
                dismissed_escalation.severity
            ),
            provider=(
                dismissed_escalation.provider
            ),
            capability=(
                dismissed_escalation.capability
            ),
            message=(
                dismissed_escalation.message
            ),
            recommendation=(
                dismissed_escalation.recommendation
            ),
            created_at=(
                dismissed_escalation.created_at
            ),
            status=(
                EscalationStatus.DISMISSED
            ),
        )
    )

    summaries = (
        type_service.get_summary()
    )

    summary_by_type = {
        summary.escalation_type: summary
        for summary in summaries
    }

    provider_failure = summary_by_type[
        EscalationType.PROVIDER_FAILURE
    ]

    assert provider_failure.total_count == 4

    assert provider_failure.active_count == 2


def test_empty_repository_returns_zero_counts() -> None:
    """
    Validate the empty Operations Center state.
    """

    (
        _,
        type_service,
        _,
    ) = create_services()

    summaries = (
        type_service.get_summary()
    )

    for summary in summaries:
        assert summary.total_count == 0
        assert summary.active_count == 0


def test_type_service_is_read_only() -> None:
    """
    Validate that generating the summary does not
    modify repository data.
    """

    (
        escalation_service,
        type_service,
        repository,
    ) = create_services()

    escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.QUALITY_DROP
            ),
            severity=(
                EscalationSeverity.HIGH
            ),
            provider="openai",
            capability="conversation",
            message="Quality decreased.",
        )
    )

    type_service.get_summary()

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