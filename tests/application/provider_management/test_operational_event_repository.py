"""
Tests for the operational event repository.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.operational_event import (
    OperationalEvent,
    OperationalEventSeverity,
    OperationalEventType,
)

from app.application.provider_management.operational_event_repository import (
    InMemoryOperationalEventRepository,
)


def create_event(
    *,
    minute: int,
    message: str,
) -> OperationalEvent:
    """
    Create deterministic operational event data.
    """

    return OperationalEvent.create(
        event_type=(
            OperationalEventType
            .AGENT_EXECUTION_FAILED
        ),
        severity=(
            OperationalEventSeverity.ERROR
        ),
        source="external_agent_runtime",
        component="conversation_agent",
        occurred_at=datetime(
            2026,
            8,
            16,
            12,
            minute,
            tzinfo=timezone.utc,
        ),
        message=message,
        correlation_id="run-001",
        metadata={
            "provider": "openai",
        },
    )


def test_repository_starts_empty() -> None:
    """
    Validate initial repository state.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    assert repository.get_all() == ()


def test_repository_saves_and_retrieves_event() -> None:
    """
    Validate persistence and retrieval by event ID.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    event = create_event(
        minute=1,
        message="Execution failed.",
    )

    repository.save(event)

    assert (
        repository.get_by_id(
            event.event_id
        )
        == event
    )


def test_repository_returns_none_for_unknown_event() -> None:
    """
    Validate unknown event lookup.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    event = create_event(
        minute=1,
        message="Execution failed.",
    )

    assert (
        repository.get_by_id(
            event.event_id
        )
        is None
    )


def test_repository_orders_events_deterministically() -> None:
    """
    Validate chronological event retrieval.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    second = create_event(
        minute=2,
        message="Second event.",
    )

    first = create_event(
        minute=1,
        message="First event.",
    )

    repository.save(second)
    repository.save(first)

    events = repository.get_all()

    assert events == (
        first,
        second,
    )


def test_repository_replaces_event_with_same_id() -> None:
    """
    Validate repository identity semantics.

    Operational events normally have unique IDs. If the same
    ID is persisted again, the repository retains the latest
    supplied representation.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    event = create_event(
        minute=1,
        message="Original event.",
    )

    repository.save(event)
    repository.save(event)

    events = repository.get_all()

    assert len(events) == 1
    assert events[0] == event


def test_none_event_is_rejected() -> None:
    """
    Validate repository input protection.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    with pytest.raises(
        ValueError,
        match="Operational event cannot be None.",
    ):
        repository.save(
            None,  # type: ignore[arg-type]
        )


def test_none_event_id_is_rejected() -> None:
    """
    Validate event ID input protection.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Operational event ID cannot be None."
        ),
    ):
        repository.get_by_id(None)


def test_clear_removes_all_events() -> None:
    """
    Validate repository reset behaviour.
    """

    repository = (
        InMemoryOperationalEventRepository()
    )

    repository.save(
        create_event(
            minute=1,
            message="Execution failed.",
        )
    )

    repository.clear()

    assert repository.get_all() == ()