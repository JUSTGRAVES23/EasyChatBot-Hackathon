from __future__ import annotations

import pytest

from app.infrastructure.email.authentication_email_sender import (
    AuthenticationEmailSenderAdapter,
)


class StubEmailProviderManager:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    async def send(
        self,
        subject: str,
        content: dict,
    ) -> dict:
        self.calls.append((subject, content))
        return self.result


@pytest.mark.asyncio
async def test_send_delegates_to_shared_provider_manager() -> None:
    provider_manager = StubEmailProviderManager(
        {
            "provider": "resend",
            "status": "accepted",
            "message_id": "msg_123",
        }
    )
    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    content = {
        "recipient": "user@example.com",
        "email_type": "authentication_verification",
        "from": "EasyChatBot <noreply@example.com>",
        "body": "Verify your email.",
        "html": "<p>Verify your email.</p>",
    }

    result = await adapter.send(
        "Verify your EasyChatBot email",
        content,
    )

    assert result == {
        "provider": "resend",
        "status": "accepted",
        "message_id": "msg_123",
    }
    assert provider_manager.calls == [
        (
            "Verify your EasyChatBot email",
            content,
        )
    ]


@pytest.mark.asyncio
async def test_send_strips_subject_before_delegation() -> None:
    provider_manager = StubEmailProviderManager({"status": "accepted"})
    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    await adapter.send(
        "  Verify your email  ",
        {"recipient": "user@example.com"},
    )

    assert provider_manager.calls[0][0] == "Verify your email"


@pytest.mark.asyncio
async def test_send_rejects_empty_subject() -> None:
    provider_manager = StubEmailProviderManager({"status": "accepted"})
    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    with pytest.raises(ValueError, match="Email subject cannot be empty"):
        await adapter.send(
            "   ",
            {"recipient": "user@example.com"},
        )

    assert provider_manager.calls == []


@pytest.mark.asyncio
async def test_send_rejects_non_dict_content() -> None:
    provider_manager = StubEmailProviderManager({"status": "accepted"})
    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    with pytest.raises(
        TypeError,
        match="Email content must be a dictionary",
    ):
        await adapter.send(
            "Verify your email",
            "invalid",  # type: ignore[arg-type]
        )

    assert provider_manager.calls == []


@pytest.mark.asyncio
async def test_send_rejects_missing_recipient() -> None:
    provider_manager = StubEmailProviderManager({"status": "accepted"})
    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    with pytest.raises(ValueError, match="Email recipient is required"):
        await adapter.send(
            "Verify your email",
            {},
        )

    assert provider_manager.calls == []


@pytest.mark.asyncio
async def test_send_rejects_blank_recipient() -> None:
    provider_manager = StubEmailProviderManager({"status": "accepted"})
    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    with pytest.raises(ValueError, match="Email recipient is required"):
        await adapter.send(
            "Verify your email",
            {"recipient": "   "},
        )

    assert provider_manager.calls == []


@pytest.mark.asyncio
async def test_send_rejects_invalid_provider_result() -> None:
    provider_manager = StubEmailProviderManager(
        {"status": "accepted"},
    )
    provider_manager.result = "invalid"  # type: ignore[assignment]

    adapter = AuthenticationEmailSenderAdapter(
        provider_manager=provider_manager,
    )

    with pytest.raises(
        TypeError,
        match="Email provider returned an invalid result",
    ):
        await adapter.send(
            "Verify your email",
            {"recipient": "user@example.com"},
        )

    assert len(provider_manager.calls) == 1
