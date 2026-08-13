import pytest

from backend.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)

from backend.providers.llm.openai_provider import (
    OpenAIProvider,
)


def test_factory_creates_openai_provider():

    provider = (
        LLMProviderFactory.create(
            "openai"
        )
    )

    assert isinstance(
        provider,
        OpenAIProvider,
    )


def test_factory_rejects_unknown_provider():

    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider",
    ):
        LLMProviderFactory.create(
            "unknown"
        )


def test_factory_rejects_empty_provider():

    with pytest.raises(
        ValueError,
        match="Provider name cannot be empty",
    ):
        LLMProviderFactory.create(
            ""
        )