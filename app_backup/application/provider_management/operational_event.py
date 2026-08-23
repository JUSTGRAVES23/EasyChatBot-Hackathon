"""
EasyChatBot AI Operations Center operational event contract.

Defines the immutable operational facts that can be emitted by
the Runtime, provider-management services, and future agent
framework integrations.

Architecture:

Agent / Runtime / Provider Service
                |
                v
        OperationalEvent
                |
                v
     Operational Event Service
                |
                v
       Operations Center


Responsibilities:

- define a stable operational event contract;
- define supported event categories;
- define operational severity;
- carry correlation and structured metadata;
- remain independent from HTTP, persistence, providers,
  agents, and Runtime implementation details.

Does NOT:

- execute agents;
- execute providers;
- change Runtime routing;
- create autonomous actions;
- persist events;
- send notifications;
- approve escalations.

Operational events represent FACTS, not COMMANDS.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


class OperationalEventType(str, Enum):
    """
    Supported categories of operational facts.
    """

    PROVIDER_HEALTH_CHANGED = (
        "provider_health_changed"
    )

    PROVIDER_INCIDENT_CREATED = (
        "provider_incident_created"
    )

    PROVIDER_RECOVERED = (
        "provider_recovered"
    )

    ESCALATION_CREATED = (
        "escalation_created"
    )

    ESCALATION_APPROVAL_REQUIRED = (
        "escalation_approval_required"
    )

    AGENT_EXECUTION_FAILED = (
        "agent_execution_failed"
    )

    AGENT_EXECUTION_COMPLETED = (
        "agent_execution_completed"
    )


class OperationalEventSeverity(str, Enum):
    """
    Operational severity associated with an event.
    """

    INFO = "info"

    WARNING = "warning"

    ERROR = "error"

    CRITICAL = "critical"


@dataclass(frozen=True)
class OperationalEvent:
    """
    Immutable operational fact.

    Events are deliberately generic so that both the future
    internal AI Operations/Quality framework and the external
    AI Agents framework can emit the same operational contract
    without being coupled to the Operations Center implementation.

    Metadata is structured context only. It must not contain
    executable commands or instructions.
    """

    event_type: OperationalEventType

    severity: OperationalEventSeverity

    source: str

    component: str

    occurred_at: datetime

    message: str

    event_id: UUID

    correlation_id: str | None

    metadata: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        event_type: OperationalEventType,
        severity: OperationalEventSeverity,
        source: str,
        component: str,
        occurred_at: datetime,
        message: str,
        correlation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "OperationalEvent":
        """
        Create a validated operational event.

        A new UUID is generated for every event.

        The event timestamp must be timezone-aware so that
        operational events remain unambiguous across environments.
        """

        if not source.strip():
            raise ValueError(
                "Operational event source "
                "cannot be empty."
            )

        if not component.strip():
            raise ValueError(
                "Operational event component "
                "cannot be empty."
            )

        if not message.strip():
            raise ValueError(
                "Operational event message "
                "cannot be empty."
            )

        if occurred_at.tzinfo is None:
            raise ValueError(
                "Operational event timestamp "
                "must be timezone-aware."
            )

        if (
            correlation_id is not None
            and not correlation_id.strip()
        ):
            raise ValueError(
                "Operational event correlation ID "
                "cannot be empty."
            )

        event_metadata = (
            {}
            if metadata is None
            else dict(metadata)
        )

        return cls(
            event_type=event_type,
            severity=severity,
            source=source.strip(),
            component=component.strip(),
            occurred_at=occurred_at,
            message=message.strip(),
            event_id=uuid4(),
            correlation_id=(
                correlation_id.strip()
                if correlation_id is not None
                else None
            ),
            metadata=MappingProxyType(
                event_metadata
            ),
        )