import pytest

from intelligence.intelligence_context import (
    IntelligenceContext,
    IntelligenceSource,
)


def test_intelligence_context_creation():
    source = IntelligenceSource(
        title="European Commission",
        url="https://example.com",
        source="European Commission",
        content="AI regulation information.",
    )

    context = IntelligenceContext(
        query="latest European AI regulation",
        sources=(source,),
        summary="Current regulatory information.",
    )

    assert context.query == (
        "latest European AI regulation"
    )

    assert context.source_count == 1

    assert context.has_sources is True

    assert context.has_summary is True


def test_intelligence_context_is_immutable():
    context = IntelligenceContext(
        query="latest AI news",
    )

    with pytest.raises(
        AttributeError
    ):
        context.query = "changed"


def test_intelligence_context_rejects_empty_query():
    with pytest.raises(
        ValueError,
        match="Intelligence query cannot be empty",
    ):
        IntelligenceContext(
            query="",
        )


def test_intelligence_source_requires_title():
    with pytest.raises(
        ValueError,
        match="title cannot be empty",
    ):
        IntelligenceSource(
            title="",
            url="https://example.com",
            source="example",
        )


def test_intelligence_context_to_context_text():
    source = IntelligenceSource(
        title="AI Regulation",
        url="https://example.com/ai",
        source="Example",
        content="European AI regulation information.",
    )

    context = IntelligenceContext(
        query="latest European AI regulation",
        sources=(source,),
        summary="Regulatory developments.",
    )

    text = context.to_context_text()

    assert "LIVE INTELLIGENCE" in text

    assert (
        "latest European AI regulation"
        in text
    )

    assert "AI Regulation" in text

    assert "https://example.com/ai" in text

    assert "European AI regulation information." in text
