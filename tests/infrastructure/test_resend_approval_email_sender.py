from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.app.application.privacy.privacy_approval_email_service import (
    ApprovalEmailRequest,
)
from backend.app.infrastructure.email.resend_approval_email_sender import (
    ResendApprovalEmailSender,
)


def make_request() -> ApprovalEmailRequest:
    return ApprovalEmailRequest(
        change_id="PCR-TEST-001",
        recipient="davdbarbero1999@gmail.com",
        subject="[EasyChatBot Privacy Governance] Approval Required",
        body=(
            "EasyChatBot Beta 1 Privacy Governance Review\n"
            "\n"
            "Explicit human approval is required."
        ),
        requires_dpo_approval=True,
        requires_grc_approval=True,
    )


def test_resend_sender_sends_expected_payload() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    request = make_request()

    with patch(
        "backend.app.infrastructure.email."
        "resend_approval_email_sender.resend.Emails.send"
    ) as mock_send:
        sender.send(request)

    mock_send.assert_called_once_with(
        {
            "from": "privacy@example.com",
            "to": ["davdbarbero1999@gmail.com"],
            "subject": (
                "[EasyChatBot Privacy Governance] "
                "Approval Required"
            ),
            "text": (
                "EasyChatBot Beta 1 Privacy Governance Review\n"
                "\n"
                "Explicit human approval is required."
            ),
        }
    )


def test_resend_sender_requires_api_key() -> None:
    sender = ResendApprovalEmailSender(
        api_key="",
        sender_email="privacy@example.com",
    )

    with pytest.raises(
        RuntimeError,
        match="RESEND_API_KEY",
    ):
        sender.send(make_request())


def test_resend_sender_requires_sender_email() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="",
    )

    with pytest.raises(
        RuntimeError,
        match="PRIVACY_APPROVAL_EMAIL_FROM",
    ):
        sender.send(make_request())


def test_resend_sender_rejects_none_request() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    with pytest.raises(
        ValueError,
        match="request cannot be None",
    ):
        sender.send(None)  # type: ignore[arg-type]


def test_resend_sender_surfaces_provider_failure() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    with patch(
        "backend.app.infrastructure.email."
        "resend_approval_email_sender.resend.Emails.send",
        side_effect=Exception("provider unavailable"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Resend privacy approval email delivery failed",
        ):
            sender.send(make_request())


def test_resend_sender_does_not_change_governance_state() -> None:
    """Infrastructure adapter only delivers email.

    Governance decisions remain owned by PrivacyGovernanceGate.
    """

    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    request = make_request()

    with patch(
        "backend.app.infrastructure.email."
        "resend_approval_email_sender.resend.Emails.send"
    ) as mock_send:
        sender.send(request)

    assert request.requires_dpo_approval is True
    assert request.requires_grc_approval is True

    mock_send.assert_called_once()