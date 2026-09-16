from __future__ import annotations

from pathlib import Path

import pytest

from app.application.identity.authentication_email_service import (
    AuthenticationEmailService,
)


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def send(self, subject: str, content: dict) -> dict:
        self.calls.append((subject, content))
        return {"status": "sent"}


def build_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[AuthenticationEmailService, RecordingSender]:
    monkeypatch.setattr(
        "app.application.identity.authentication_email_service._registration_email_sender",
        lambda: "academy@easychatbotacademy.com",
    )

    logo_path = tmp_path / "easychatbot-logo.png"
    logo_path.write_bytes(b"logo")

    sender = RecordingSender()

    service = AuthenticationEmailService(
        sender,
        frontend_base_url="https://academy.example.com/",
        privacy_url="https://academy.example.com/privacy",
        logo_path=logo_path,
    )

    return service, sender


@pytest.mark.asyncio
async def test_password_reset_email_uses_new_subject_and_recipient(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email=" user@example.com ",
        username="David",
        reset_token="reset-token-123",
    )

    subject, content = sender.calls[0]

    assert subject == "Reset your EasyChatBot password"
    assert content["recipient"] == "user@example.com"
    assert content["email_type"] == "authentication_password_reset"
    assert content["from"] == "academy@easychatbotacademy.com"


@pytest.mark.asyncio
async def test_password_reset_email_has_responsive_html_cta(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token="raw-reset-token-456",
    )

    _, content = sender.calls[0]

    expected_url = (
        "https://academy.example.com/"
        "reset-password?token=raw-reset-token-456"
    )

    html = content["html"]

    assert "<!DOCTYPE html>" in html
    assert 'name="viewport"' in html
    assert "EasyChatBot" in html
    assert "Growing With You." in html
    assert "Reset your password" in html
    assert "We received a request to reset the password" in html
    assert "Reset password" in html
    assert f'href="{expected_url}"' in html


@pytest.mark.asyncio
async def test_password_reset_email_contains_security_guidance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token="reset-token-security",
    )

    _, content = sender.calls[0]

    html = content["html"]
    body = content["body"]

    for value in (
        "expires after a limited period",
        "can only be used once",
        "Didn't request this?",
        "You can safely ignore this email",
        "Your password will not change unless you use the reset link.",
    ):
        assert value in html

    for value in (
        "This link expires after a limited period",
        "can only be used once",
        "If you did not request this",
        "Your password will not change unless you use the reset link.",
    ):
        assert value in body


@pytest.mark.asyncio
async def test_password_reset_email_has_plain_text_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token="reset-token-text",
    )

    _, content = sender.calls[0]

    expected_url = (
        "https://academy.example.com/"
        "reset-password?token=reset-token-text"
    )

    assert isinstance(content["body"], str)
    assert content["body"].strip()
    assert "Reset your password" in content["body"]
    assert expected_url in content["body"]


@pytest.mark.asyncio
async def test_password_reset_email_has_no_attachments_or_image_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token="reset-token-assets",
    )

    _, content = sender.calls[0]
    html = content["html"]

    assert content["attachments"] == []

    assert "<img" not in html.lower()
    assert "cid:" not in html.lower()
    assert "<map" not in html.lower()
    assert "<area" not in html.lower()

    # The email must not contain the old fixed artwork dimensions.
    assert 'width="1024"' not in html
    assert 'height="1536"' not in html


@pytest.mark.asyncio
async def test_password_reset_email_has_real_accessible_button(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token="reset-token-button",
    )

    _, content = sender.calls[0]
    html = content["html"]

    assert '<a' in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "Reset password" in html
    assert "background-color:#1680ff" in html


@pytest.mark.asyncio
async def test_password_reset_email_escapes_dynamic_html_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username='<David & "Learner">',
        reset_token="reset-token-safe",
    )

    _, content = sender.calls[0]

    html = content["html"]

    assert "&lt;David &amp; &quot;Learner&quot;&gt;" in html
    assert '<David & "Learner">' not in html


@pytest.mark.asyncio
async def test_password_reset_email_url_encodes_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token="token/with unsafe value",
    )

    _, content = sender.calls[0]

    html = content["html"]
    body = content["body"]

    expected_url = (
        "https://academy.example.com/"
        "reset-password?token=token%2Fwith%20unsafe%20value"
    )

    assert expected_url in html
    assert expected_url in body


@pytest.mark.asyncio
async def test_password_reset_email_does_not_expose_token_as_separate_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(monkeypatch, tmp_path)

    raw_token = "sensitive-reset-token-987"

    await service.send_password_reset_email(
        email="user@example.com",
        username="David",
        reset_token=raw_token,
    )

    _, content = sender.calls[0]

    assert "reset_token" not in content
    assert "token_hash" not in content

    # The token is present only where it must be: inside the reset URL.
    expected_url = (
        "https://academy.example.com/"
        f"reset-password?token={raw_token}"
    )

    assert content["html"].count(raw_token) == 1
    assert content["body"].count(raw_token) == 1
    assert expected_url in content["html"]
    assert expected_url in content["body"]
