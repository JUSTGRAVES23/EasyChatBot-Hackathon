"""
AI Runtime capability contracts.

This module defines the provider-independent contract used by
the AI Runtime to request execution of an approved capability.

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

This module contains contracts only.

It does not:
- execute agents
- call providers
- evaluate governance policies
- perform external side effects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class CapabilityType(StrEnum):
    """
    Supported runtime capability categories.

    The list is intentionally small for the initial framework
    implementation. New capabilities should be added explicitly.
    """

    LIVE_INTELLIGENCE = "live_intelligence"
    LEARNING_GENERATION = "learning_generation"
    EVALUATION = "evaluation"


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
    Provider-independent request submitted to the AI Runtime.

    Attributes:
        capability:
            Logical capability requested by the application.

        request_id:
            Correlation identifier for the execution.

        payload:
            Explicit capability input.

        metadata:
            Non-business execution metadata.

        requested_by:
            Component or application requesting execution.
    """

    capability: CapabilityType
    request_id: str
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
    requested_by: str = "application"

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError(
                "Capability request_id cannot be empty."
            )

        if not self.requested_by.strip():
            raise ValueError(
                "Capability requested_by cannot be empty."
            )


@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """
    Provider-independent result returned by the AI Runtime.

    The result contains execution information but does not expose
    provider-specific response objects.
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
        Return True when execution was rejected before execution.
        """

        return (
            self.status
            == CapabilityExecutionStatus.REJECTED
        )