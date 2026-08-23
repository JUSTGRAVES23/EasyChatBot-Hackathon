"""
EasyChatBot AI Operations Center escalation notification tests.

Validates:

Provider Escalation
        |
        v
EscalationNotificationService
        |
        v
Email Notification Adapter
        |
        v
Prepared Human Notification

No real email is sent.

No provider routing is changed.

No escalation is approved automatically.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.email_notification_adapter import (
    InMemoryEmailNotificationAdapter,
)

from app.application.provider_management.escalation_notification_service import (
    EscalationNotificationService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationType,
    ProviderEscalation,
)


def create_escalation() -> ProviderEscalation:
    """
    Create a deterministic provider failure escalation.
    """

    return ProviderEscalation(
        escalation_id="esc-001",
        escalation_type=(
            EscalationType.PROVIDER_FAILURE
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="openai",
        capability="conversation",
        message=(
            "Provider openai is currently unavailable. "
            "Affected capabilities: conversation. "
            "Consecutive health failures: 3."
        ),
        recommendation=(
            "Review alternative providers for "
            "conversation workloads. "
            "Human approval is required."
        ),
        created_at=datetime(
            2026,
            8,
            14,
            14,
            34,
            tzinfo=timezone.utc,
        ),
    )


def create_service() -> (
    EscalationNotificationService
):
    """
    Create the notification service with the in-memory
    email adapter.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    return EscalationNotificationService(
        email_adapter=adapter
    )


def test_escalation_notification_is_prepared() -> None:
    """
    Validate preparation of a human escalation
    notification.
    """

    service = create_service()

    result = (
        service.prepare_escalation_notification(
            escalation=create_escalation(),
            recipient="operations@example.com",
        )
    )

    assert (
        result.escalation_id
        == "esc-001"
    )

    assert (
        result.recipient
        == "operations@example.com"
    )

    assert (
        "AI Operations Escalation"
        in result.subject
    )

    assert (
        "HIGH"
        in result.subject
    )

    assert (
        "esc-001"
        in result.body
    )

    assert (
        "provider_failure"
        in result.body
    )

    assert (
        "openai"
        in result.body
    )

    assert (
        "conversation"
        in result.body
    )


def test_recipient_is_trimmed() -> None:
    """
    Validate safe recipient normalisation.
    """

    service = create_service()

    result = (
        service.prepare_escalation_notification(
            escalation=create_escalation(),
            recipient=(
                "  operations@example.com  "
            ),
        )
    )

    assert (
        result.recipient
        == "operations@example.com"
    )


def test_none_escalation_is_rejected() -> None:
    """
    Validate required escalation input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Provider escalation cannot be None."
        ),
    ):
        service.prepare_escalation_notification(
            escalation=None,  # type: ignore[arg-type]
            recipient="operations@example.com",
        )


def test_empty_recipient_is_rejected() -> None:
    """
    Validate required notification recipient.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Notification recipient cannot be empty."
        ),
    ):
        service.prepare_escalation_notification(
            escalation=create_escalation(),
            recipient="   ",
        )


def test_notification_preserves_human_approval_requirement() -> None:
    """
    Validate that the prepared notification retains the
    human approval requirement.
    """

    service = create_service()

    result = (
        service.prepare_escalation_notification(
            escalation=create_escalation(),
            recipient="operations@example.com",
        )
    )

    body = result.body.lower()

    assert "human" in body
    assert "approval" in body


def test_notification_does_not_change_escalation() -> None:
    """
    Validate that notification preparation does not mutate
    the immutable escalation contract.
    """

    escalation = create_escalation()

    service = create_service()

    result = (
        service.prepare_escalation_notification(
            escalation=escalation,
            recipient="operations@example.com",
        )
    )

    assert (
        result.escalation_id
        == escalation.escalation_id
    )

    assert (
        escalation.provider
        == "openai"
    )

    assert (
        escalation.severity
        == EscalationSeverity.HIGH
    )

    assert (
        escalation.escalation_type
        == EscalationType.PROVIDER_FAILURE
    )