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
        case_id="CASE-TEST-001",
        change_id="PCR-TEST-001",
        recipient="davdbarbero1999@gmail.com",
        subject=(
            "[EasyChatBot Privacy Governance] "
            "Approval Required"
        ),
        body=(
            "EasyChatBot Beta 1 Privacy Governance Review\n"
            "\n"
            "Explicit human approval is required."
        ),
        requires_dpo_approval=True,
        requires_grc_approval=True,
    )


@pytest.mark.asyncio
async def test_resend_sender_sends_expected_payload() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    request = make_request()

    mock_response = {
        "id": "MSG-TEST-001",
    }

    with patch(
        "backend.app.infrastructure.email."
        "resend_approval_email_sender.resend.Emails.send",
        return_value=mock_response,
    ) as mock_send:
        result = await sender.send(request)

    mock_send.assert_called_once_with(
        {
            "from": "privacy@example.com",
            "to": [
                "davdbarbero1999@gmail.com"
            ],
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

    assert result["status"] == "accepted"
    assert result["reference"] == "MSG-TEST-001"
    assert result["message_id"] == "MSG-TEST-001"
    assert result["case_id"] == "CASE-TEST-001"
    assert result["change_id"] == "PCR-TEST-001"


@pytest.mark.asyncio
async def test_resend_sender_requires_api_key() -> None:
    sender = ResendApprovalEmailSender(
        api_key="",
        sender_email="privacy@example.com",
    )

    with pytest.raises(
        RuntimeError,
        match="RESEND_API_KEY",
    ):
        await sender.send(make_request())


@pytest.mark.asyncio
async def test_resend_sender_requires_sender_email() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="",
    )

    with pytest.raises(
        RuntimeError,
        match="PRIVACY_APPROVAL_EMAIL_FROM",
    ):
        await sender.send(make_request())


@pytest.mark.asyncio
async def test_resend_sender_rejects_none_request() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    with pytest.raises(
        ValueError,
        match="request cannot be None",
    ):
        await sender.send(None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_resend_sender_surfaces_provider_failure() -> None:
    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    with patch(
        "backend.app.infrastructure.email."
        "resend_approval_email_sender.resend.Emails.send",
        side_effect=Exception(
            "provider unavailable"
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match=(
                "Resend privacy approval email "
                "delivery failed"
            ),
        ):
            await sender.send(make_request())


@pytest.mark.asyncio
async def test_resend_sender_does_not_change_governance_state() -> None:
    """Infrastructure adapter only delivers email.

    Governance decisions remain owned by the governance
    decision service / gate.
    """

    sender = ResendApprovalEmailSender(
        api_key="re_test_key",
        sender_email="privacy@example.com",
    )

    request = make_request()

    with patch(
        "backend.app.infrastructure.email."
        "resend_approval_email_sender.resend.Emails.send",
        return_value={
            "id": "MSG-TEST-002",
        },
    ) as mock_send:
        result = await sender.send(request)

    assert request.requires_dpo_approval is True
    assert request.requires_grc_approval is True

    assert result["case_id"] == "CASE-TEST-001"
    assert result["change_id"] == "PCR-TEST-001"

    mock_send.assert_called_once()