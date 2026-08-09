"""
Tests for Search Provider Interface.

Validates:
- SearchResult data model behaviour
- SearchProvider abstract contract
"""

import pytest

from src.providers.search_provider.interface import (
    SearchProvider,
    SearchResult,
)


def test_search_result_creation():
    """
    SearchResult should store normalised provider output.
    """

    result = SearchResult(
        title="AI Act Update",
        url="https://example.com/article",
        content="Latest AI regulation news.",
        source="example",
    )

    assert result.title == "AI Act Update"
    assert result.url == "https://example.com/article"
    assert result.content == "Latest AI regulation news."
    assert result.source == "example"


def test_search_result_is_immutable():
    """
    SearchResult is frozen and should not allow mutation.
    """

    result = SearchResult(
        title="Test",
        url="https://example.com",
        content="Content",
        source="test",
    )

    with pytest.raises(AttributeError):
        result.title = "Changed"


def test_search_provider_cannot_be_instantiated():
    """
    SearchProvider is an abstract interface.
    """

    with pytest.raises(TypeError):
        SearchProvider()