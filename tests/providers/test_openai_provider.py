"""
Tests for OpenAIProvider.

These tests never call the real OpenAI API.

The OpenAI AsyncOpenAI client is injected with a fake client
so provider behaviour can be tested deterministically.
"""

from types import SimpleNamespace

import pytest

from backend.conversation.conversation_request import (
    ConversationRequest,
)

from backend.providers.llm.openai_provider import (
    OpenAIProvider,
)


class FakeResponses:
    """Fake OpenAI Responses API."""

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.response = response
        self.error = error
        self.received_kwargs = None

    async def create(
        self,
        **kwargs,
    ):
        self.received_kwargs = kwargs

        if self.error is not None:
            raise self.error

        return self.response


class FakeOpenAIClient:
    """Fake AsyncOpenAI client."""

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.responses = FakeResponses(
            response=response,
            error=error,
        )


def create_request(
    *,
    context=None,
):
    """Create a valid conversation request."""

    return ConversationRequest(
        system_instruction=(
            "You are Yeti, a friendly AI companion."
        ),
        user_prompt=(
            "Explain artificial intelligence."
        ),
        conversation_context=context,
        character_id="yeti",
        character_name="Yeti",
    )


def test_openai_provider_initialises():
    """Provider should initialise with a valid model."""

    client = FakeOpenAIClient()

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    assert provider.provider_id == "openai"
    assert provider.model == "gpt-5-mini"


def test_openai_provider_rejects_empty_model():
    """Provider should reject an empty model identifier."""

    client = FakeOpenAIClient()

    with pytest.raises(
        ValueError,
        match="OpenAI model cannot be empty",
    ):
        OpenAIProvider(
            model="",
            client=client,
        )


@pytest.mark.asyncio
async def test_openai_provider_generates_response():
    """Successful OpenAI response should become ProviderResult."""

    response = SimpleNamespace(
        output_text="Artificial intelligence is the field of AI.",
    )

    client = FakeOpenAIClient(
        response=response,
    )

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    result = await provider.generate(
        create_request(),
    )

    assert result.success is True
    assert result.provider_id == "openai"
    assert (
        result.output
        == "Artificial intelligence is the field of AI."
    )
    assert result.error is None


@pytest.mark.asyncio
async def test_openai_provider_builds_correct_request():
    """Provider should correctly translate ConversationRequest."""

    response = SimpleNamespace(
        output_text="Test response.",
    )

    client = FakeOpenAIClient(
        response=response,
    )

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    request = create_request(
        context=(
            "LIVE INTELLIGENCE\n"
            "Research query: AI regulation"
        ),
    )

    result = await provider.generate(
        request,
    )

    assert result.success is True

    sent = (
        client.responses.received_kwargs
    )

    assert sent is not None

    assert sent["model"] == "gpt-5-mini"

    messages = sent["input"]

    assert messages[0] == {
        "role": "system",
        "content": (
            "You are Yeti, a friendly AI companion."
        ),
    }

    assert messages[1] == {
        "role": "user",
        "content": (
            "Additional context:\n"
            "LIVE INTELLIGENCE\n"
            "Research query: AI regulation"
        ),
    }

    assert messages[2] == {
        "role": "user",
        "content": (
            "Explain artificial intelligence."
        ),
    }


@pytest.mark.asyncio
async def test_openai_provider_without_context():
    """Provider should not create a context message when absent."""

    response = SimpleNamespace(
        output_text="Test response.",
    )

    client = FakeOpenAIClient(
        response=response,
    )

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    result = await provider.generate(
        create_request(),
    )

    assert result.success is True

    messages = (
        client.responses.received_kwargs["input"]
    )

    assert len(messages) == 2

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


@pytest.mark.asyncio
async def test_openai_provider_handles_api_error():
    """OpenAI exceptions should become failed ProviderResult."""

    client = FakeOpenAIClient(
        error=RuntimeError(
            "OpenAI service unavailable"
        ),
    )

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    result = await provider.generate(
        create_request(),
    )

    assert result.success is False
    assert result.provider_id == "openai"
    assert result.output is None
    assert (
        result.error
        == "OpenAI service unavailable"
    )


@pytest.mark.asyncio
async def test_openai_provider_handles_empty_response():
    """Empty OpenAI output should produce a failed result."""

    response = SimpleNamespace(
        output_text="",
    )

    client = FakeOpenAIClient(
        response=response,
    )

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    result = await provider.generate(
        create_request(),
    )

    assert result.success is False
    assert result.provider_id == "openai"
    assert result.output is None
    assert (
        result.error
        == "OpenAI returned an empty response."
    )


@pytest.mark.asyncio
async def test_openai_provider_rejects_none_request():
    """Provider should reject a missing conversation request."""

    client = FakeOpenAIClient()

    provider = OpenAIProvider(
        model="gpt-5-mini",
        client=client,
    )

    with pytest.raises(
        ValueError,
        match="Conversation request cannot be None",
    ):
        await provider.generate(None)