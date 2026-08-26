"""Provider-independent WS-22.3.1 publication execution contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID


class PublicationExecutionStatus(str, Enum):
    """Outcome of a publication execution attempt."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    IDEMPOTENT_REPLAY = "idempotent_replay"


@dataclass(frozen=True, slots=True)
class PublicationExecutionRequest:
    """Immutable command to execute an already-approved publication."""

    publication_id: UUID
    idempotency_key: str
    actor: str
    correlation_id: str

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key cannot be empty.")
        if not self.actor.strip():
            raise ValueError("actor cannot be empty.")
        if not self.correlation_id.strip():
            raise ValueError("correlation_id cannot be empty.")


@dataclass(frozen=True, slots=True)
class PublicationExecutionResult:
    """Provider-neutral result returned by the execution service."""

    publication_id: UUID
    status: PublicationExecutionStatus
    idempotency_key: str
    correlation_id: str
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class AnnouncementPublisher(Protocol):
    """Port implemented by infrastructure/channel adapters.

    No Telegram, Discord, email, or other provider types belong here.
    """

    async def publish(
        self,
        *,
        publication_id: UUID,
        title: str,
        content: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> str | None:
        """Publish and return an optional provider message identifier."""
