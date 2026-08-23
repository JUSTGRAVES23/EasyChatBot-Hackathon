from __future__ import annotations

import pytest

from app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)


class FakeConversationRuntime:
    def __init__(self) -> None:
        self.calls = []

    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
    ) -> str:
        self.calls.append(
            {
                "character_instruction": character_instruction,
                "learner_message": learner_message,
            }
        )

        return "Bonjour, bienvenue à l'Académie EasyChatBot."


@pytest.mark.asyncio
async def test_telegram_conversation_service_delegates_to_runtime():
    runtime = FakeConversationRuntime()

    service = TelegramConversationService(
        conversation_runtime=runtime,
    )

    response = await service.handle_telegram_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == (
        "Bonjour, bienvenue à l'Académie EasyChatBot."
    )

    assert len(runtime.calls) == 1

    assert runtime.calls[0]["learner_message"] == (
        "Bonjour"
    )

    assert "EasyChatBot Academy" in (
        runtime.calls[0]["character_instruction"]
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_rejects_empty_message():
    runtime = FakeConversationRuntime()

    service = TelegramConversationService(
        conversation_runtime=runtime,
    )

    with pytest.raises(ValueError):
        await service.handle_telegram_message(
            telegram_user_id=12345,
            message="",
        )


def test_telegram_conversation_service_requires_runtime():
    with pytest.raises(ValueError):
        TelegramConversationService(
            conversation_runtime=None,
        )