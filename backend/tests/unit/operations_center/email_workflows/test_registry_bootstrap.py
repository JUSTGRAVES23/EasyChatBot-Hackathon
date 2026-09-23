from datetime import datetime, timezone

import pytest

from app.application.operations_center.email_workflows.domain import (
    EmailWorkflowLifecycle,
)
from app.application.operations_center.email_workflows.in_memory_registry import (
    InMemoryEmailWorkflowRegistry,
)
from app.application.operations_center.email_workflows.registry_bootstrap import (
    EmailWorkflowRegistryBootstrap,
)


def test_bootstrap_creates_validated_built_in_workflows():
    registry = InMemoryEmailWorkflowRegistry()

    result = EmailWorkflowRegistryBootstrap(registry).ensure_registered(
        now=datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    )

    assert result.created == (
        "cybersecurity_daily_report",
        "cybersecurity_weekly_report",
        "cybersecurity_critical_alert",
        "platform_intelligence_escalation",
    )

    assert (
        registry.get("cybersecurity_daily_report").schedule
        == "daily_08:00"
    )
    assert (
        registry.get("cybersecurity_weekly_report").schedule
        == "weekly_monday_08:00"
    )
    assert (
        registry.get("cybersecurity_critical_alert").schedule
        is None
    )

    platform_intelligence = registry.get(
        "platform_intelligence_escalation"
    )

    assert platform_intelligence is not None
    assert platform_intelligence.schedule is None
    assert (
        platform_intelligence.lifecycle
        is EmailWorkflowLifecycle.ACTIVE
    )
    assert platform_intelligence.owner == "platform_intelligence"
    assert platform_intelligence.trigger == "escalation_recommendation"
    assert (
        platform_intelligence.template_id
        == "platform_intelligence_escalation"
    )

    assert (
        registry.get("cybersecurity_daily_report").lifecycle
        is EmailWorkflowLifecycle.ACTIVE
    )


def test_bootstrap_is_idempotent_and_does_not_overwrite():
    registry = InMemoryEmailWorkflowRegistry()
    bootstrap = EmailWorkflowRegistryBootstrap(registry)

    first = bootstrap.ensure_registered(
        now=datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    )

    before = registry.get("cybersecurity_daily_report")

    second = bootstrap.ensure_registered(
        now=datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc)
    )

    after = registry.get("cybersecurity_daily_report")

    assert len(first.created) == 4
    assert second.created == ()
    assert len(second.already_present) == 4
    assert before == after


def test_bootstrap_rejects_naive_clock():
    registry = InMemoryEmailWorkflowRegistry()

    with pytest.raises(ValueError, match="timezone-aware"):
        EmailWorkflowRegistryBootstrap(registry).ensure_registered(
            now=datetime(2026, 9, 18, 20, 0)
        )