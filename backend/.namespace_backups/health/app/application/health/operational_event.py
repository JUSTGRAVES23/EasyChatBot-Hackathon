from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class OperationalSurface(str, Enum):
    """
    Operational surface being monitored.

    Private classroom and announcement-group operations
    remain explicitly separated.
    """

    PRIVATE_CLASSROOM = "private_classroom"
    ANNOUNCEMENT_GROUP = "announcement_group"


class OperationalEventType(str, Enum):
    """Supported operational event categories."""

    MESSAGE_FAILURE = "message_failure"
    RATE_LIMIT = "rate_limit"
    ABUSE = "abuse"
    PROVIDER_FAILURE = "provider_failure"
    DATABASE_FAILURE = "database_failure"
    TELEGRAM_FAILURE = "telegram_failure"
    NOTIFICATION_FAILURE = "notification_failure"


class OperationalSeverity(str, Enum):
    """Operational incident severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True)
class OperationalEvent:
    """
    Sanitized operational event.

    The event intentionally contains operational metadata only.

    It must never contain:
        - learner message content
        - prompts
        - model responses
        - passwords
        - API keys
        - database URLs
        - Telegram bot tokens
    """

    event_type: OperationalEventType
    surface: OperationalSurface
    correlation_id: str

    severity: OperationalSeverity = (
        OperationalSeverity.MEDIUM
    )

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    user_reference: str | None = None
    world_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        correlation_id = (
            self.correlation_id
            .replace("\r", "")
            .replace("\n", "")
            .strip()
        )

        if not correlation_id:
            raise ValueError(
                "correlation_id cannot be empty."
            )

        object.__setattr__(
            self,
            "correlation_id",
            correlation_id,
        )

        if self.user_reference is not None:
            object.__setattr__(
                self,
                "user_reference",
                self._clean_identifier(
                    self.user_reference
                ),
            )

        if self.world_id is not None:
            object.__setattr__(
                self,
                "world_id",
                self._clean_identifier(
                    self.world_id
                ),
            )

    @staticmethod
    def _clean_identifier(
        value: str,
    ) -> str:
        return (
            str(value)
            .replace("\r", "")
            .replace("\n", "")
            .strip()
        )

    def as_dict(self) -> dict[str, Any]:
        """
        Return an operationally safe representation.

        Learner content is not part of the event contract.
        """

        return {
            "event_type": self.event_type.value,
            "surface": self.surface.value,
            "correlation_id": self.correlation_id,
            "severity": self.severity.value,
            "occurred_at": (
                self.occurred_at.isoformat()
            ),
            "user_reference": self.user_reference,
            "world_id": self.world_id,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "OperationalEvent",
    "OperationalEventType",
    "OperationalSeverity",
    "OperationalSurface",
]