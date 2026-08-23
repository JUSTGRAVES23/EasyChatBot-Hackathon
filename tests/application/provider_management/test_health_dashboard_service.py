"""
EasyChatBot AI Operations Center health dashboard tests.

Validates:

Provider Analytics
        |
        +----------------------+
        |                      |
        v                      v

Provider Health         Escalation Repository
        |                      |
        +----------+-----------+
                   |
                   v
        AIHealthDashboardService
                   |
                   v
        Dashboard Health Contract

No UI is rendered and no external systems are called.
"""

from decimal import Decimal

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)

from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)

from app.application.analytics.ai_platform.provider_analytics_service import (
    ProviderAnalyticsService,
)

from app.application.provider_management.escalation_repository import (
    InMemoryEscalationRepository,
)

from app.application.provider_management.escalation_service import (
    EscalationService,
)

from app.application.provider_management.health_dashboard_service import (
    AIHealthDashboardService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationStatus,
    EscalationType,
)


def create_usage_event(
    *,
    provider: str,
    success: bool = True,
) -> ProviderUsageEvent:
    """
    Create deterministic provider usage data.
    """

    return ProviderUsageEvent(
        provider=provider,
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=800,
        estimated_cost=Decimal("0.010"),
        quality_score=95.0,
        success=success,
    )


def create_dashboard_service(
    usage_repository: InMemoryProviderUsageRepository,
    escalation_repository: InMemoryEscalationRepository,
) -> AIHealthDashboardService:
    """
    Create the dashboard service from its dependencies.
    """

    analytics_service = ProviderAnalyticsService(
        repository=usage_repository,
    )

    return AIHealthDashboardService(
        analytics_service=analytics_service,
        escalation_repository=escalation_repository,
    )


def test_health_dashboard_reports_provider_health() -> None:
    """
    Validate provider health information.
    """

    usage_repository = (
        InMemoryProviderUsageRepository()
    )

    escalation_repository = (
        InMemoryEscalationRepository()
    )

    usage_repository.save(
        create_usage_event(
            provider="openai",
        )
    )

    usage_repository.save(
        create_usage_event(
            provider="gemini",
        )
    )

    service = create_dashboard_service(
        usage_repository,
        escalation_repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.system_confidence == 100.0

    assert dashboard.active_providers == (
        "gemini",
        "openai",
    )

    assert dashboard.monitoring_active is True

    assert dashboard.active_escalations == 0

    assert dashboard.high_priority_escalations == 0


def test_health_dashboard_counts_active_escalations() -> None:
    """
    Validate active escalation aggregation.
    """

    usage_repository = (
        InMemoryProviderUsageRepository()
    )

    escalation_repository = (
        InMemoryEscalationRepository()
    )

    usage_repository.save(
        create_usage_event(
            provider="openai",
        )
    )

    escalation_service = EscalationService(
        repository=escalation_repository,
    )

    escalation_service.create_escalation(
        escalation_type=(
            EscalationType.COST_SPIKE
        ),
        severity=(
            EscalationSeverity.MEDIUM
        ),
        provider="openai",
        capability="conversation",
        message="Provider cost increased.",
    )

    escalation_service.create_escalation(
        escalation_type=(
            EscalationType.LATENCY_DEGRADATION
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="openai",
        capability="conversation",
        message="Provider latency increased.",
    )

    service = create_dashboard_service(
        usage_repository,
        escalation_repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.active_escalations == 2

    assert (
        dashboard.high_priority_escalations
        == 1
    )


def test_resolved_escalations_are_not_active() -> None:
    """
    Validate escalation lifecycle filtering.

    Resolved and dismissed escalations must not
    appear in the active dashboard count.
    """

    usage_repository = (
        InMemoryProviderUsageRepository()
    )

    escalation_repository = (
        InMemoryEscalationRepository()
    )

    usage_repository.save(
        create_usage_event(
            provider="openai",
        )
    )

    escalation_service = EscalationService(
        repository=escalation_repository,
    )

    escalation = (
        escalation_service.create_escalation(
            escalation_type=(
                EscalationType.PROVIDER_FAILURE
            ),
            severity=(
                EscalationSeverity.CRITICAL
            ),
            provider="openai",
            capability="conversation",
            message="Provider unavailable.",
        )
    )

    resolved_escalation = (
        escalation.__class__(
            escalation_id=(
                escalation.escalation_id
            ),
            escalation_type=(
                escalation.escalation_type
            ),
            severity=(
                escalation.severity
            ),
            provider=(
                escalation.provider
            ),
            capability=(
                escalation.capability
            ),
            message=(
                escalation.message
            ),
            recommendation=(
                escalation.recommendation
            ),
            created_at=(
                escalation.created_at
            ),
            status=(
                EscalationStatus.RESOLVED
            ),
        )
    )

    escalation_repository.clear()

    escalation_repository.save(
        resolved_escalation
    )

    service = create_dashboard_service(
        usage_repository,
        escalation_repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.active_escalations == 0

    assert (
        dashboard.high_priority_escalations
        == 0
    )


def test_failed_provider_requests_reduce_system_confidence() -> None:
    """
    Validate that provider failures affect the current
    operational confidence metric.
    """

    usage_repository = (
        InMemoryProviderUsageRepository()
    )

    escalation_repository = (
        InMemoryEscalationRepository()
    )

    usage_repository.save(
        create_usage_event(
            provider="openai",
            success=True,
        )
    )

    usage_repository.save(
        create_usage_event(
            provider="openai",
            success=False,
        )
    )

    service = create_dashboard_service(
        usage_repository,
        escalation_repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.system_confidence == 50.0

    assert dashboard.active_providers == (
        "openai",
    )

    assert dashboard.monitoring_active is True