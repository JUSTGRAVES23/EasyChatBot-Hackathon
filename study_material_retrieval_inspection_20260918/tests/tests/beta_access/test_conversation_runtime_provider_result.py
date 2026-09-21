import pytest

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.providers.provider_result import ProviderResult


class FakeProvider:
    async def generate(self, *, system_prompt: str, user_message: str):
        return ProviderResult(
            success=True,
            provider_id="fake",
            model="test-model",
            content="Bonjour !",
        )


class LegacyStringProvider:
    async def generate(self, *, system_prompt: str, user_message: str):
        return "Bonjour !"


@pytest.mark.asyncio
async def test_runtime_returns_provider_result_content() -> None:
    runtime = ConversationRuntime(llm_provider=FakeProvider())
    result = await runtime.respond(
        character_instruction="You are a French teacher.",
        learner_message="Bonjour",
    )
    assert result == "Bonjour !"


@pytest.mark.asyncio
async def test_runtime_preserves_legacy_string_provider_compatibility() -> None:
    runtime = ConversationRuntime(llm_provider=LegacyStringProvider())
    result = await runtime.respond(
        character_instruction="You are a French teacher.",
        learner_message="Bonjour",
    )
    assert result == "Bonjour !"


@pytest.mark.asyncio
async def test_runtime_surfaces_provider_failure() -> None:
    class FailedProvider:
        async def generate(self, *, system_prompt: str, user_message: str):
            return ProviderResult(
                success=False,
                provider_id="fake",
                model="test-model",
                error="provider unavailable",
            )

    runtime = ConversationRuntime(llm_provider=FailedProvider())

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await runtime.respond(
            character_instruction="teacher",
            learner_message="Bonjour",
        )

