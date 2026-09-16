import pytest

from intelligence.intelligence_context import (
    IntelligenceContext,
)

from runtime.context.execution_context import (
    ExecutionContext,
)


def test_execution_context_creation():

    context = ExecutionContext(
        user_id="demo-user",
        request="Hello",
    )

    assert context.user_id == (
        "demo-user"
    )

    assert context.request == (
        "Hello"
    )

    assert context.execution_id

    assert context.created_at

    assert context.metadata == {}

    assert context.intelligence_context is None

    assert context.has_intelligence_context is False


def test_execution_context_is_immutable():

    context = ExecutionContext(
        user_id="demo-user",
        request="Hello",
    )

    with pytest.raises(
        AttributeError
    ):
        context.request = "Changed"


def test_execution_context_can_carry_intelligence():

    intelligence = IntelligenceContext(
        query="Latest European AI regulation",
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain this to me",
        intelligence_context=intelligence,
    )

    assert context.intelligence_context is intelligence

    assert context.has_intelligence_context is True

    assert (
        context.intelligence_context.query
        == "Latest European AI regulation"
    )
