"""
Tests for H3-01 MemoryContextBuilder.

The builder consumes the application-facing
MemoryRecord contract returned by MemoryService.

No LLM, provider, database, or external service is used.
"""

from backend.memory.memory_record import (
    MemoryRecord,
)

from src.ai_runtime.memory.context_builder import (
    DEFAULT_MAX_CONTEXT_CHARACTERS,
    DEFAULT_MAX_MEMORY_ITEMS,
    MemoryContextBuilder,
)


def make_memory(
    *,
    user_id: str = "user-001",
    category: str = "preference",
    content: str = (
        "Prefers technology topics."
    ),
) -> MemoryRecord:
    return MemoryRecord(
        user_id=user_id,
        category=category,
        content=content,
        created_at=__import__(
            "datetime"
        ).datetime.now(
            __import__(
                "datetime"
            ).timezone.utc
        ),
    )


def test_empty_memory_returns_empty_context() -> None:
    builder = MemoryContextBuilder()

    result = builder.build(
        user_id="user-001",
        request="European AI regulation",
        memories=[],
    )

    assert result.is_empty is True
    assert result.entries == ()
    assert result.text == ""


def test_relevant_preference_is_included() -> None:
    builder = MemoryContextBuilder()

    memory = make_memory(
        content=(
            "Prefers European AI regulation topics."
        ),
    )

    result = builder.build(
        user_id="user-001",
        request=(
            "latest European AI regulation"
        ),
        memories=[memory],
    )

    assert result.memory_count == 1
    assert result.entries == (memory,)
    assert (
        "European AI regulation"
        in result.text
    )


def test_irrelevant_memory_is_excluded() -> None:
    builder = MemoryContextBuilder()

    memory = make_memory(
        content=(
            "Prefers hiking and mountain equipment."
        ),
    )

    result = builder.build(
        user_id="user-001",
        request=(
            "latest European AI regulation"
        ),
        memories=[memory],
    )

    assert result.is_empty is True


def test_relevant_learning_goal_is_included() -> None:
    builder = MemoryContextBuilder()

    memory = make_memory(
        category="learning_goal",
        content=(
            "Improve French conversation "
            "about technology."
        ),
    )

    result = builder.build(
        user_id="user-001",
        request="French technology conversation",
        memories=[memory],
    )

    assert result.entries == (memory,)


def test_relevant_discovery_context_is_included() -> None:
    builder = MemoryContextBuilder()

    memory = make_memory(
        category="discovery_context",
        content=(
            "Previously discussed European "
            "AI regulation."
        ),
    )

    result = builder.build(
        user_id="user-001",
        request="European AI regulation",
        memories=[memory],
    )

    assert result.entries == (memory,)


def test_user_isolation_excludes_other_users() -> None:
    builder = MemoryContextBuilder()

    own_memory = make_memory(
        user_id="user-001",
        content=(
            "Prefers European AI topics."
        ),
    )

    other_memory = make_memory(
        user_id="user-002",
        content=(
            "Prefers European AI topics."
        ),
    )

    result = builder.build(
        user_id="user-001",
        request="European AI",
        memories=[
            other_memory,
            own_memory,
        ],
    )

    assert result.entries == (own_memory,)


def test_max_memory_items_is_enforced() -> None:
    builder = MemoryContextBuilder(
        max_memory_items=2,
        max_context_characters=4000,
    )

    memories = [
        make_memory(
            content=(
                f"Prefers technology topic "
                f"{index}."
            ),
        )
        for index in range(5)
    ]

    result = builder.build(
        user_id="user-001",
        request="technology topic",
        memories=memories,
    )

    assert len(result.entries) == 2


def test_max_context_characters_is_enforced() -> None:
    builder = MemoryContextBuilder(
        max_memory_items=5,
        max_context_characters=100,
    )

    memory = make_memory(
        content=(
            "Prefers European artificial "
            "intelligence regulation and "
            "technology policy."
        ),
    )

    result = builder.build(
        user_id="user-001",
        request=(
            "European artificial intelligence "
            "regulation"
        ),
        memories=[memory],
    )

    assert len(result.text) <= 100


def test_ordering_is_deterministic() -> None:
    builder = MemoryContextBuilder()

    first_memory = make_memory(
        content=(
            "Prefers European AI regulation."
        ),
    )

    second_memory = make_memory(
        content=(
            "Interested in European AI policy."
        ),
    )

    memories = [
        first_memory,
        second_memory,
    ]

    first = builder.build(
        user_id="user-001",
        request="European AI regulation",
        memories=memories,
    )

    second = builder.build(
        user_id="user-001",
        request="European AI regulation",
        memories=memories,
    )

    assert first.entries == second.entries
    assert first.text == second.text


def test_invalid_memory_is_ignored_safely() -> None:
    builder = MemoryContextBuilder()

    valid = make_memory(
        content="Prefers European AI topics.",
    )

    invalid = object()

    result = builder.build(
        user_id="user-001",
        request="European AI",
        memories=[
            invalid,  # type: ignore[list-item]
            valid,
        ],
    )

    assert result.entries == (valid,)


def test_input_collection_is_not_mutated() -> None:
    builder = MemoryContextBuilder()

    first = make_memory(
        content="Prefers European AI topics.",
    )

    second = make_memory(
        content="Prefers technology topics.",
    )

    memories = [
        first,
        second,
    ]

    original = list(memories)

    builder.build(
        user_id="user-001",
        request="European AI",
        memories=memories,
    )

    assert memories == original


def test_empty_user_id_is_rejected() -> None:
    builder = MemoryContextBuilder()

    try:
        builder.build(
            user_id="",
            request="European AI",
            memories=[],
        )
    except ValueError as exc:
        assert str(exc) == (
            "user_id cannot be empty."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_empty_request_is_rejected() -> None:
    builder = MemoryContextBuilder()

    try:
        builder.build(
            user_id="user-001",
            request="",
            memories=[],
        )
    except ValueError as exc:
        assert str(exc) == (
            "request cannot be empty."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_invalid_max_memory_items_is_rejected() -> None:
    try:
        MemoryContextBuilder(
            max_memory_items=0,
            max_context_characters=(
                DEFAULT_MAX_CONTEXT_CHARACTERS
            ),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_invalid_max_context_characters_is_rejected() -> None:
    try:
        MemoryContextBuilder(
            max_memory_items=(
                DEFAULT_MAX_MEMORY_ITEMS
            ),
            max_context_characters=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_negative_max_memory_items_is_rejected() -> None:
    try:
        MemoryContextBuilder(
            max_memory_items=-1,
            max_context_characters=(
                DEFAULT_MAX_CONTEXT_CHARACTERS
            ),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_negative_max_context_characters_is_rejected() -> None:
    try:
        MemoryContextBuilder(
            max_memory_items=(
                DEFAULT_MAX_MEMORY_ITEMS
            ),
            max_context_characters=-1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_context_is_explicitly_marked_as_learner_context() -> None:
    builder = MemoryContextBuilder()

    memory = make_memory(
        content="Prefers European AI topics.",
    )

    result = builder.build(
        user_id="user-001",
        request="European AI",
        memories=[memory],
    )

    assert result.text.startswith(
        "Learner context:"
    )

    assert "[preference]" in result.text