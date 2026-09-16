"""
AI Runtime capability contracts.

This module defines the provider-independent contracts used by
the AI Runtime to request and represent execution of approved
capabilities.

Architecture:

Application
    |
    v
AI Runtime
    |
    v
Capability Request
    |
    v
Governance
    |
    v
Capability Execution
    |
    v
Capability Result


This module contains contracts only.

It does not:

- execute agents;
- call providers;
- evaluate governance policies;
- perform external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from src.ai_runtime.capabilities.actor_context import RuntimeActorContext


class CapabilityType(StrEnum):
    """
    Supported AI Runtime capability categories.

    Capabilities are explicit Runtime contracts.

    Adding a new capability requires:

    - registration;
    - governance review;
    - executor implementation;
    - testing.

    The capability itself does not imply autonomous execution.
    """

    LIVE_INTELLIGENCE = (
        "live_intelligence"
    )

    PODCAST_DISCOVERY = (
        "podcast_discovery"
    )

    PODCAST_LISTENING_PROPOSAL = (
        "podcast_listening_proposal"
    )

    LEARNING_GENERATION = (
        "learning_generation"
    )

    FLASHCARD_GENERATION = (
        "flashcard_generation"
    )

    INTERNAL_DOCUMENTATION_SEARCH = (
        "internal_documentation_search"
    )

    INTERNAL_DATA_READ = (
        "internal_data_read"
    )

    EVALUATION = (
        "evaluation"
    )


# =========================================================
# Backward Compatibility
# =========================================================

"""
Historical Runtime/application code imports:

    CapabilityName

The contract was renamed to:

    CapabilityType

Keep this alias during migration.
"""

CapabilityName = CapabilityType


class CapabilityExecutionStatus(StrEnum):
    """
    Runtime-level execution status.
    """

    ACCEPTED = "accepted"

    COMPLETED = "completed"

    REJECTED = "rejected"

    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    """
    Provider-independent request submitted to AI Runtime.

    The application/API boundary may provide either:

    - CapabilityType enum values;
    - string capability values.

    Strings are normalised to CapabilityType internally.

    Actor context is optional for backward compatibility.

    When present, RuntimeActorContext provides the authenticated
    actor context required for governed capability execution.
    """

    capability: CapabilityType

    request_id: str

    payload: Mapping[str, Any]

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    requested_by: str = "application"

    actor: RuntimeActorContext | None = None

    def __post_init__(self) -> None:
        """
        Validate and normalise the Runtime request.
        """

        if not isinstance(
            self.request_id,
            str,
        ):
            raise ValueError(
                "Capability request_id must be a string."
            )

        if not self.request_id.strip():
            raise ValueError(
                "Capability request_id cannot be empty."
            )

        if not isinstance(
            self.requested_by,
            str,
        ):
            raise ValueError(
                "Capability requested_by must be a string."
            )

        if not self.requested_by.strip():
            raise ValueError(
                "Capability requested_by cannot be empty."
            )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise ValueError(
                "Capability payload must be a mapping."
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise ValueError(
                "Capability metadata must be a mapping."
            )

        if self.actor is not None and not isinstance(
            self.actor,
            RuntimeActorContext,
        ):
            raise ValueError(
                "Capability actor must be a valid "
                "RuntimeActorContext."
            )

        if isinstance(
            self.capability,
            str,
        ):
            try:
                object.__setattr__(
                    self,
                    "capability",
                    CapabilityType(
                        self.capability,
                    ),
                )

            except ValueError as exc:
                raise ValueError(
                    "Unsupported capability: "
                    f"{self.capability}"
                ) from exc

        elif not isinstance(
            self.capability,
            CapabilityType,
        ):
            raise ValueError(
                "Capability must be a valid CapabilityType."
            )


@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """
    Provider-independent result returned by AI Runtime.

    Provider-specific responses remain hidden behind
    capability executors.
    """

    request_id: str

    capability: CapabilityType

    status: CapabilityExecutionStatus

    output: Any = None

    error: str | None = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def succeeded(self) -> bool:
        """
        Return True when execution completed successfully.
        """

        return (
            self.status
            == CapabilityExecutionStatus.COMPLETED
        )

    @property
    def failed(self) -> bool:
        """
        Return True when execution failed.
        """

        return (
            self.status
            == CapabilityExecutionStatus.FAILED
        )

    @property
    def rejected(self) -> bool:
        """
        Return True when governance rejected execution.
        """

        return (
            self.status
            == CapabilityExecutionStatus.REJECTED
        )