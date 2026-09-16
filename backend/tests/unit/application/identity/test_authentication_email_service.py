from __future__ import annotations

from pathlib import Path

import pytest

from app.application.identity.authentication_email_service import (
    AuthenticationEmailService,
)


class StubAuthenticationEmailSender:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def send(
        self,
        subject: str,
        content: dict,
    ) -> dict:
        self.calls.append((subject, content))
        return {
            "provider": "stub",
            "status": "accepted",
        }


def build_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    privacy_url: str | None = None,
) -> tuple[AuthenticationEmailService, StubAuthenticationEmailSender]:
    monkeypatch.setattr(
        "app.application.identity.authentication_email_service."
        "_registration_email_sender",
        lambda: "EasyChatBot <noreply@example.com>",
    )

    logo_path = tmp_path / "easychatbot-logo.png"
    logo_path.write_bytes(b"fake-logo")

    sender = StubAuthenticationEmailSender()

    service = AuthenticationEmailService(
        sender,
        frontend_base_url="https://academy.example.com/",
        privacy_url=privacy_url,
        logo_path=logo_path,
    )

    return service, sender


@pytest.mark.asyncio
async def test_send_verification_email_includes_privacy_url_when_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(
        monkeypatch,
        tmp_path,
        privacy_url="https://academy.example.com/privacy",
    )

    result = await service.send_verification_email(
        email="user@example.com",
        username="David",
        verification_token="test-token",
    )

    assert result == {
        "provider": "stub",
        "status": "accepted",
    }

    assert len(sender.calls) == 1

    _, content = sender.calls[0]

    assert content["recipient"] == "user@example.com"
    assert "https://academy.example.com/privacy" in content["html"]
    assert "https://academy.example.com/privacy" in content["body"]
    assert "Data Protection" in content["html"]


@pytest.mark.asyncio
async def test_send_verification_email_omits_privacy_section_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(
        monkeypatch,
        tmp_path,
        privacy_url=None,
    )

    result = await service.send_verification_email(
        email="user@example.com",
        username="David",
        verification_token="test-token",
    )

    assert result["status"] == "accepted"

    _, content = sender.calls[0]

    assert (
        "https://academy.example.com/verify-email?token=test-token"
        in content["html"]
    )
    assert (
        "https://academy.example.com/verify-email?token=test-token"
        in content["body"]
    )

    assert "Data Protection &amp; Privacy" not in content["html"]
    assert "Data Protection & Privacy" not in content["body"]


@pytest.mark.asyncio
async def test_blank_privacy_url_is_treated_as_not_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, sender = build_service(
        monkeypatch,
        tmp_path,
        privacy_url="   ",
    )

    await service.send_verification_email(
        email="user@example.com",
        username="David",
        verification_token="test-token",
    )

    _, content = sender.calls[0]

    assert "Data Protection &amp; Privacy" not in content["html"]
    assert "Data Protection & Privacy" not in content["body"]


@pytest.mark.asyncio
async def test_privacy_url_is_optional_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.application.identity.authentication_email_service."
        "_registration_email_sender",
        lambda: "EasyChatBot <noreply@example.com>",
    )

    logo_path = tmp_path / "easychatbot-logo.png"
    logo_path.write_bytes(b"fake-logo")

    sender = StubAuthenticationEmailSender()

    service = AuthenticationEmailService(
        sender,
        frontend_base_url="https://academy.example.com",
        logo_path=logo_path,
    )

    await service.send_verification_email(
        email="user@example.com",
        username="David",
        verification_token="test-token",
    )

    assert len(sender.calls) == 1

    _, content = sender.calls[0]

    assert "Data Protection &amp; Privacy" not in content["html"]
    assert "Data Protection & Privacy" not in content["body"]