"""
AI Service Provider Manager email notification tests.

Validates:

Provider Escalation
        |
        v
Email Notification Adapter
        |
        v
Prepared Human Notification

No real email is sent.

The adapter must:

- prepare a notification;
- preserve escalation information;
- require a recipient;
- remain independent of the email provider.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.email_notification_adapter import (
    InMemoryEmailNotificationAdapter,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationStatus,
    EscalationType,
    ProviderEscalation,
)


def create_escalation() -> ProviderEscalation:
    """
    Create a deterministic escalation for testing.
    """

    return ProviderEscalation(
        escalation_id="esc-001",
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
        created_at=datetime(
            2026,
            8,
            14,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        status=(
            EscalationStatus.OPEN
        ),
    )


def test_escalation_email_is_prepared() -> None:
    """
    Validate preparation of a human escalation email.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    escalation = create_escalation()

    email = (
        adapter.prepare_escalation_email(
            escalation=escalation,
            recipient="operations@example.com",
        )
    )

    assert (
        email.recipient
        == "operations@example.com"
    )

    assert (
        "AI Operations Escalation"
        in email.subject
    )

    assert (
        "HIGH"
        in email.subject
    )

    assert (
        "esc-001"
        in email.body
    )

    assert (
    "latency_degradation"
    in email.body
    )

    assert (
        "openai"
        in email.body
    )

    assert (
        "conversation"
        in email.body
    )

    assert (
        "GPT-5-mini latency increased"
        in email.body
    )

    assert (
        "Review alternative providers"
        in email.body
    )


def test_prepared_email_is_retained_for_inspection() -> None:
    """
    Validate that the development adapter retains
    prepared notifications for inspection.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    escalation = create_escalation()

    adapter.prepare_escalation_email(
        escalation=escalation,
        recipient="operations@example.com",
    )

    emails = (
        adapter.get_prepared_emails()
    )

    assert len(emails) == 1

    assert (
        emails[0].recipient
        == "operations@example.com"
    )


def test_multiple_emails_are_retained() -> None:
    """
    Validate multiple escalation notifications.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    escalation = create_escalation()

    adapter.prepare_escalation_email(
        escalation=escalation,
        recipient="operations@example.com",
    )

    adapter.prepare_escalation_email(
        escalation=escalation,
        recipient="backup@example.com",
    )

    emails = (
        adapter.get_prepared_emails()
    )

    assert len(emails) == 2

    assert (
        emails[0].recipient
        == "operations@example.com"
    )

    assert (
        emails[1].recipient
        == "backup@example.com"
    )


def test_none_escalation_is_rejected() -> None:
    """
    Validate escalation input.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    with pytest.raises(
        ValueError,
        match="Escalation cannot be None.",
    ):
        adapter.prepare_escalation_email(
            escalation=None,  # type: ignore[arg-type]
            recipient="operations@example.com",
        )


def test_empty_recipient_is_rejected() -> None:
    """
    Validate recipient input.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    escalation = create_escalation()

    with pytest.raises(
        ValueError,
        match=(
            "Email recipient cannot be empty."
        ),
    ):
        adapter.prepare_escalation_email(
            escalation=escalation,
            recipient="",
        )


def test_clear_removes_prepared_emails() -> None:
    """
    Validate test/development storage cleanup.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    escalation = create_escalation()

    adapter.prepare_escalation_email(
        escalation=escalation,
        recipient="operations@example.com",
    )

    adapter.clear()

    assert (
        adapter.get_prepared_emails()
        == []
    )