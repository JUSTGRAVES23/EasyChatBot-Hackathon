"""
Tests for the Resend email provider.

The provider supports two controlled email contracts:

1. Cybersecurity notifications
   -> existing cybersecurity HTML renderer.

2. Privacy Governance reminders
   -> application-owned HTML and inline logo attachment.

These tests ensure the provider boundary does not mix
the two presentation contracts.
"""

from __future__ import annotations

import base64

import pytest
import resend

from cybersecurity.email.resend_email_provider import (
    ResendEmailProvider,
)


def test_resend_provider_requires_api_key_when_configuration_missing(
    monkeypatch,
):
    """
    Provider must reject missing API credentials when no
    configured environment value exists.
    """

    monkeypatch.setattr(
        "backend.cybersecurity.email.resend_email_provider.RESEND_API_KEY",
        "",
    )

    with pytest.raises(ValueError):
        ResendEmailProvider(
            api_key=None,
            sender="EasyChatBot <test@example.com>",
        )


def test_resend_provider_requires_sender_when_configuration_missing(
    monkeypatch,
):
    """
    Provider must reject missing sender configuration when no
    configured sender exists.
    """

    monkeypatch.setattr(
        "backend.cybersecurity.email.resend_email_provider.EMAIL_FROM",
        "",
    )

    with pytest.raises(ValueError):
        ResendEmailProvider(
            api_key="test-api-key",
            sender=None,
        )


def test_resend_provider_has_expected_identity():
    """
    Provider exposes its stable provider identifier.
    """

    provider = ResendEmailProvider(
        api_key="test-api-key",
        sender="EasyChatBot <test@example.com>",
    )

    assert provider.provider_id == "resend"


@pytest.mark.asyncio
async def test_resend_provider_rejects_empty_subject():
    """
    Provider must reject an empty email subject.
    """

    provider = ResendEmailProvider(
        api_key="test-api-key",
        sender="EasyChatBot <test@example.com>",
    )

    with pytest.raises(ValueError):
        await provider.send(
            "",
            {
                "recipient": "test@example.com",
            },
        )


@pytest.mark.asyncio
async def test_resend_provider_requires_recipient():
    """
    Provider must reject email payloads without a recipient.
    """

    provider = ResendEmailProvider(
        api_key="test-api-key",
        sender="EasyChatBot <test@example.com>",
    )

    with pytest.raises(ValueError):
        await provider.send(
            "Test",
            {},
        )


def test_resend_provider_builds_security_html():
    """
    Provider must render the important cybersecurity
    intelligence fields into the email HTML.
    """

    html = ResendEmailProvider._build_html(
        {
            "posture": "HIGH ATTENTION REQUIRED",
            "critical_count": 0,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "signal_count": 4,
            "open_signal_count": 4,
            "priority_signals": [
                {
                    "title": "Prompt injection detected",
                    "severity": "high",
                }
            ],
            "decision_note": (
                "Review the highest-priority signals."
            ),
            "execution_id": "test-execution",
            "data_mode": "DEMO",
        }
    )

    assert "HIGH ATTENTION REQUIRED" in html

    assert (
        "Prompt injection detected"
        in html
    )

    assert "DEMO" in html

    assert (
        "decision support only"
        in html
    )

    assert (
        "No remediation action was executed"
        in html
    )


@pytest.mark.asyncio
async def test_privacy_governance_reminder_uses_supplied_html(
    monkeypatch,
):
    """
    Privacy Governance reminders must use the application-owned
    html_body rather than the Cybersecurity renderer.
    """

    captured: dict[str, object] = {}

    class FakeResponse:
        id = "msg-privacy-governance-test"

    async def fake_send_async(params):
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(
        resend.Emails,
        "send_async",
        fake_send_async,
    )

    provider = ResendEmailProvider(
        api_key="test-api-key",
        sender="EasyChatBot <test@example.com>",
    )

    supplied_html = """
    <html>
        <body>
            <h1>EasyChatBot Privacy Governance</h1>
            <p>CASE-E2E-001</p>
            <p>PCR-E2E-001</p>
            <a href="http://127.0.0.1:5173/privacy-governance/CASE-E2E-001">
                REVIEW THIS CASE
            </a>
        </body>
    </html>
    """

    result = await provider.send(
        "[EasyChatBot Privacy Governance] Reminder",
        {
            "recipient": "reviewer@example.com",
            "body": (
                "Review CASE-E2E-001 for PCR-E2E-001."
            ),
            "html_body": supplied_html,
            "email_type": "privacy_governance_reminder",
        },
    )

    assert result["provider"] == "resend"
    assert result["status"] == "accepted"
    assert result["message_id"] == (
        "msg-privacy-governance-test"
    )

    params = captured["params"]

    assert isinstance(params, dict)

    assert params["html"] == supplied_html

    assert (
        "EasyChatBot Cybersecurity Notification"
        not in params["html"]
    )


@pytest.mark.asyncio
async def test_privacy_governance_inline_attachment_uses_base64_content(
    monkeypatch,
    tmp_path,
):
    """
    Privacy Governance inline assets must be sent as base64 content.

    Resend does not accept a local Windows filesystem path as the
    attachment path. The provider must therefore convert the local
    file into attachment content before calling Resend.
    """

    logo = tmp_path / "easychatbot_logo.png"

    logo_bytes = b"fake-png-content"

    logo.write_bytes(logo_bytes)

    captured: dict[str, object] = {}

    class FakeResponse:
        id = "msg-privacy-logo-test"

    async def fake_send_async(params):
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(
        resend.Emails,
        "send_async",
        fake_send_async,
    )

    provider = ResendEmailProvider(
        api_key="test-api-key",
        sender="EasyChatBot <test@example.com>",
    )

    result = await provider.send(
        "[EasyChatBot Privacy Governance] Reminder",
        {
            "recipient": "reviewer@example.com",
            "body": (
                "Review CASE-E2E-001."
            ),
            "html_body": (
                '<img src="cid:easychatbot-governance-logo">'
            ),
            "email_type": "privacy_governance_reminder",
            "attachments": [
                {
                    "path": str(logo),
                    "filename": "easychatbot_logo.png",
                    "content_id": (
                        "easychatbot-governance-logo"
                    ),
                    "inline": True,
                }
            ],
        },
    )

    assert result["status"] == "accepted"

    params = captured["params"]

    assert isinstance(params, dict)

    attachments = params["attachments"]

    assert isinstance(attachments, list)
    assert len(attachments) == 1

    attachment = attachments[0]

    assert "path" not in attachment

    assert (
        attachment["filename"]
        == "easychatbot_logo.png"
    )

    assert (
        attachment["content_id"]
        == "easychatbot-governance-logo"
    )

    expected_content = base64.b64encode(
        logo_bytes
    ).decode("ascii")

    assert (
        attachment["content"]
        == expected_content
    )


@pytest.mark.asyncio
async def test_privacy_governance_rejects_missing_html_body():
    """
    Privacy Governance reminders must provide their own HTML.
    """

    provider = ResendEmailProvider(
        api_key="test-api-key",
        sender="EasyChatBot <test@example.com>",
    )

    with pytest.raises(TypeError):
        await provider.send(
            "Privacy Governance Reminder",
            {
                "recipient": "reviewer@example.com",
                "body": "Review the case.",
                "email_type": (
                    "privacy_governance_reminder"
                ),
            },
        )
