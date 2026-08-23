"""
Tests for the OperationalEvent contract.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.operational_event import (
    OperationalEvent,
    OperationalEventSeverity,
    OperationalEventType,
)


def create_event() -> OperationalEvent:
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
            0,
            tzinfo=timezone.utc,
        ),
        message="Agent execution failed.",
        correlation_id="run-001",
        metadata={
            "provider": "openai",
            "capability": "conversation",
        },
    )


def test_operational_event_is_created() -> None:
    """
    Validate creation of a valid operational event.
    """

    event = create_event()

    assert (
        event.event_type
        == OperationalEventType
        .AGENT_EXECUTION_FAILED
    )

    assert (
        event.severity
        == OperationalEventSeverity.ERROR
    )

    assert (
        event.source
        == "external_agent_runtime"
    )

    assert (
        event.component
        == "conversation_agent"
    )

    assert (
        event.correlation_id
        == "run-001"
    )

    assert (
        event.metadata["provider"]
        == "openai"
    )


def test_operational_event_has_unique_id() -> None:
    """
    Validate that every event receives its own identity.
    """

    first = create_event()
    second = create_event()

    assert (
        first.event_id
        != second.event_id
    )


def test_operational_event_is_immutable() -> None:
    """
    Validate that the event contract is immutable.
    """

    event = create_event()

    with pytest.raises(
        TypeError,
    ):
        event.metadata["provider"] = "gemini"


def test_empty_source_is_rejected() -> None:
    """
    Validate required source input.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operational event source "
            "cannot be empty."
        ),
    ):
        OperationalEvent.create(
            event_type=(
                OperationalEventType
                .AGENT_EXECUTION_FAILED
            ),
            severity=(
                OperationalEventSeverity.ERROR
            ),
            source="   ",
            component="agent",
            occurred_at=datetime.now(
                timezone.utc
            ),
            message="Failure.",
        )


def test_empty_component_is_rejected() -> None:
    """
    Validate required component input.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operational event component "
            "cannot be empty."
        ),
    ):
        OperationalEvent.create(
            event_type=(
                OperationalEventType
                .AGENT_EXECUTION_FAILED
            ),
            severity=(
                OperationalEventSeverity.ERROR
            ),
            source="runtime",
            component="   ",
            occurred_at=datetime.now(
                timezone.utc
            ),
            message="Failure.",
        )


def test_empty_message_is_rejected() -> None:
    """
    Validate required message input.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operational event message "
            "cannot be empty."
        ),
    ):
        OperationalEvent.create(
            event_type=(
                OperationalEventType
                .AGENT_EXECUTION_FAILED
            ),
            severity=(
                OperationalEventSeverity.ERROR
            ),
            source="runtime",
            component="agent",
            occurred_at=datetime.now(
                timezone.utc
            ),
            message="   ",
        )


def test_naive_timestamp_is_rejected() -> None:
    """
    Validate timezone-aware operational timestamps.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operational event timestamp "
            "must be timezone-aware."
        ),
    ):
        OperationalEvent.create(
            event_type=(
                OperationalEventType
                .AGENT_EXECUTION_FAILED
            ),
            severity=(
                OperationalEventSeverity.ERROR
            ),
            source="runtime",
            component="agent",
            occurred_at=datetime(
                2026,
                8,
                16,
                12,
                0,
            ),
            message="Failure.",
        )


def test_empty_correlation_id_is_rejected() -> None:
    """
    Validate optional correlation ID semantics.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operational event correlation ID "
            "cannot be empty."
        ),
    ):
        OperationalEvent.create(
            event_type=(
                OperationalEventType
                .AGENT_EXECUTION_FAILED
            ),
            severity=(
                OperationalEventSeverity.ERROR
            ),
            source="runtime",
            component="agent",
            occurred_at=datetime.now(
                timezone.utc
            ),
            message="Failure.",
            correlation_id="   ",
        )


def test_metadata_is_copied_on_creation() -> None:
    """
    Validate that external metadata mutation cannot alter
    the event's stored metadata.
    """

    metadata = {
        "provider": "openai",
    }

    event = OperationalEvent.create(
        event_type=(
            OperationalEventType
            .AGENT_EXECUTION_COMPLETED
        ),
        severity=(
            OperationalEventSeverity.INFO
        ),
        source="runtime",
        component="agent",
        occurred_at=datetime.now(
            timezone.utc
        ),
        message="Execution completed.",
        metadata=metadata,
    )

    metadata["provider"] = "gemini"

    assert (
        event.metadata["provider"]
        == "openai"
    )