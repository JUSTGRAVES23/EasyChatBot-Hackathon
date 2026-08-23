"""
Tests for the cybersecurity email provider manager.
"""

import pytest

from backend.cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


class FakeEmailProvider:

    provider_id = "fake"

    async def send(
        self,
        subject: str,
        content: dict,
    ) -> dict:

        return {
            "provider": self.provider_id,
            "status": "accepted",
            "message_id": "test-message-id",
        }


@pytest.mark.asyncio
async def test_provider_manager_uses_injected_provider():

    provider = FakeEmailProvider()

    manager = EmailProviderManager(
        provider=provider,
    )

    result = await manager.send(
        "Test subject",
        {
            "recipient": "test@example.com",
        },
    )

    assert result["provider"] == "fake"
    assert result["status"] == "accepted"
    assert result["message_id"] == "test-message-id"


@pytest.mark.asyncio
async def test_provider_manager_reports_provider_not_configured(
    monkeypatch,
):

    monkeypatch.setattr(
        EmailProviderManager,
        "_build_default_provider",
        staticmethod(
            lambda: None
        ),
    )

    manager = EmailProviderManager()

    result = await manager.send(
        "Test subject",
        {
            "recipient": "test@example.com",
        },
    )

    assert result == {
        "status": "provider_not_configured",
    }


def test_provider_manager_builds_resend_provider_when_configured():

    manager = EmailProviderManager()

    assert manager.provider is not None

    assert (
        manager.provider.provider_id
        == "resend"
    )


def test_provider_manager_status_when_resend_is_configured():

    manager = EmailProviderManager()

    status = manager.status()

    assert status["provider"] == "resend"
    assert status["configured"] is True
    assert status["available"] is True
    assert status["status"] == "ready"


def test_provider_manager_status_when_provider_is_not_configured(
    monkeypatch,
):

    monkeypatch.setattr(
        EmailProviderManager,
        "_build_default_provider",
        staticmethod(
            lambda: None
        ),
    )

    manager = EmailProviderManager()

    status = manager.status()

    assert status["provider"] is None
    assert status["configured"] is False
    assert status["available"] is False
    assert status["status"] == "not_configured"


def test_provider_manager_status_does_not_expose_credentials():

    manager = EmailProviderManager()

    status = manager.status()

    assert "api_key" not in status
    assert "resend_api_key" not in status
    assert "secret" not in status
    assert "password" not in status