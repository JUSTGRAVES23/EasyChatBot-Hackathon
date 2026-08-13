"""
API provider wiring integration tests.

Verifies that the API composition layer creates an
LLMService through the LLMProviderFactory and injects
that service into ConversationAgent.

The real OpenAI API is never called.
"""

import pytest

from backend.api import routes
from backend.characters.character_profile import (
    CharacterProfile,
)
from backend.providers.provider_result import (
    ProviderResult,
)
from backend.services.llm_service import (
    LLMService,
)


class FakeProvider:
    """
    Deterministic provider used by the integration test.
    """

    def __init__(self):
        self.received_request = None

    async def generate(
        self,
        request,
    ):
        self.received_request = request

        return ProviderResult(
            success=True,
            provider_id="fake_llm",
            output="Fake AI response",
        )


class FakeConversationAgent:
    """
    Test double for ConversationAgent.

    Captures the injected LLMService so the API
    composition boundary can be verified.
    """

    def __init__(
        self,
        character,
        llm_service=None,
    ):
        self.character = character
        self.llm_service = llm_service


def create_character():
    """
    Create deterministic test character.
    """

    return CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description=(
            "Friendly AI learning companion"
        ),
        personality=(
            "Curious and encouraging"
        ),
        learning_style=(
            "Conversation based learning"
        ),
    )


def test_create_companion_service_injects_llm_service(
    monkeypatch,
):
    """
    Verify API composition creates an LLMService
    through the provider factory and injects it
    into ConversationAgent.
    """

    captured = {}

    def fake_factory_create(
        provider="openai",
    ):
        fake_provider = FakeProvider()

        captured["provider"] = fake_provider
        captured["provider_name"] = provider

        return fake_provider

    def fake_conversation_agent(
        character,
        llm_service=None,
    ):
        agent = FakeConversationAgent(
            character=character,
            llm_service=llm_service,
        )

        captured["character"] = character
        captured["agent"] = agent
        captured["llm_service"] = llm_service

        return agent

    monkeypatch.setattr(
        routes.LLMProviderFactory,
        "create",
        staticmethod(
            fake_factory_create
        ),
    )

    monkeypatch.setattr(
        routes,
        "ConversationAgent",
        fake_conversation_agent,
    )

    character = (
        routes.character_registry.get(
            "yeti"
        )
    )

    service = (
        routes.create_companion_service(
            character
        )
    )

    assert service is not None

    assert (
        captured["character"]
        == character
    )

    assert (
        captured["llm_service"]
        is not None
    )

    assert isinstance(
        captured["llm_service"],
        LLMService,
    )

    assert (
        captured["provider"]
        is captured[
            "llm_service"
        ].llm_provider
    )

    assert (
        captured["provider_name"]
        == "openai"
    )

    assert (
        captured["agent"].llm_service
        is captured["llm_service"]
    )