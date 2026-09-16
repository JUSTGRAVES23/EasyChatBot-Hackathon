import pytest

from app.providers.provider_result import (
    ProviderResult,
    ProviderUsage,
)


def test_provider_usage_allows_unknown_metrics() -> None:
    usage = ProviderUsage()
    assert usage.input_tokens is None
    assert usage.output_tokens is None
    assert usage.total_tokens is None


def test_provider_usage_rejects_negative_tokens() -> None:
    with pytest.raises(ValueError, match="input_tokens cannot be negative"):
        ProviderUsage(input_tokens=-1)


def test_provider_result_has_output_compatibility_alias() -> None:
    result = ProviderResult(
        success=True,
        provider_id="ollama",
        model="test-model",
        content="Bonjour",
    )
    assert result.content == "Bonjour"
    assert result.output == "Bonjour"


def test_failed_provider_result_requires_error() -> None:
    with pytest.raises(ValueError, match="requires an error"):
        ProviderResult(
            success=False,
            provider_id="ollama",
            model="test-model",
        )

