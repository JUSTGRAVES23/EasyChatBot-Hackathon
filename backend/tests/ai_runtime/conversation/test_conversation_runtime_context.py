from __future__ import annotations

import pytest

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
    ConversationRuntimeContext,
    ConversationTurn,
)
from app.providers.llm.llm_provider import LLMProvider
from app.providers.provider_result import ProviderResult


class CapturingProvider(LLMProvider):
    def __init__(self) -> None:
        self.system_prompt = None
        self.user_message = None

    async def generate(self, *, system_prompt: str, user_message: str):
        self.system_prompt = system_prompt
        self.user_message = user_message
        return ProviderResult(
            success=True,
            provider_id="fake",
            model="test-model",
            content="response",
        )


@pytest.mark.asyncio
async def test_runtime_composes_authoritative_context() -> None:
    provider = CapturingProvider()
    runtime = ConversationRuntime(llm_provider=provider)

    context = ConversationRuntimeContext(
        world_id="french_world",
        world_name="French World",
        language_code="fr",
        world_type="language",
        learning_domain="language_learning",
        response_language="fr",
        history=(
            ConversationTurn(role="user", content="Bonjour"),
            ConversationTurn(role="assistant", content="Bonjour !"),
        ),
    )

    result = await runtime.respond(
        character_instruction="You are Alix.",
        learner_message="Comment allez-vous ?",
        context=context,
    )

    assert result == "response"
    assert provider.system_prompt is not None
    assert "You are Alix." in provider.system_prompt
    assert "French World" in provider.system_prompt
    assert "french_world" in provider.system_prompt
    assert "language_learning" in provider.system_prompt
    assert "Response language: fr" in provider.system_prompt

    assert provider.user_message is not None
    assert "[Persisted conversation history]" in provider.user_message
    assert "USER: Bonjour" in provider.user_message
    assert "ASSISTANT: Bonjour !" in provider.user_message
    assert "[Current learner message]" in provider.user_message
    assert "Comment allez-vous ?" in provider.user_message


@pytest.mark.asyncio
async def test_runtime_preserves_legacy_call_without_context() -> None:
    provider = CapturingProvider()
    runtime = ConversationRuntime(llm_provider=provider)

    result = await runtime.respond(
        character_instruction="teacher",
        learner_message="Bonjour",
    )

    assert result == "response"
    assert provider.system_prompt == "teacher"
    assert provider.user_message == "Bonjour"


def test_runtime_context_validates_turn_role() -> None:
    with pytest.raises(ValueError, match="role"):
        ConversationTurn(role="system", content="do something")


def test_runtime_context_validates_required_world_fields() -> None:
    with pytest.raises(ValueError, match="world_id"):
        ConversationRuntimeContext(
            world_id="",
            world_name="French World",
            language_code="fr",
            world_type="language",
            learning_domain="language_learning",
            response_language="fr",
        )
