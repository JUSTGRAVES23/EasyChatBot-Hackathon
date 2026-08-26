"""WS-22.3.1 provider/channel-independent ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.app.domain.announcement_publication.execution import (
    PublishAnnouncementCommand,
    PublicationExecutionResult,
)


@dataclass(frozen=True, slots=True)
class PublicationForExecution:
    """Minimal execution projection required by the use case.

    The adapter/application layer can map the existing WS-22.1
    publication model into this projection without coupling the execution
    engine to a specific channel provider.
    """

    publication_id: str
    status: str
    destination: str
    rendered_content: str


class PublicationExecutionRepository(Protocol):
    """Port for loading and recording publication execution state."""

    async def get_for_execution(
        self,
        publication_id: str,
    ) -> PublicationForExecution | None:
        ...

    async def record_execution(
        self,
        result: PublicationExecutionResult,
    ) -> None:
        ...


class PublicationPublisher(Protocol):
    """Provider/channel-neutral publishing port."""

    async def publish(
        self,
        *,
        publication: PublicationForExecution,
        idempotency_key: str,
    ) -> str:
        """Publish and return an opaque provider reference.

        Implementations must not expose credentials through the result.
        """
        ...


class PublicationAuditSink(Protocol):
    """Port for durable/observable publication audit events."""

    async def record(self, event: object) -> None:
        ...


class PublicationIdempotencyStore(Protocol):
    """Port preventing duplicate external publication attempts."""

    async def get_result(
        self,
        idempotency_key: str,
    ) -> PublicationExecutionResult | None:
        ...

    async def store_result(
        self,
        result: PublicationExecutionResult,
    ) -> None:
        ...


__all__ = [
    "PublicationAuditSink",
    "PublicationExecutionRepository",
    "PublicationExecutionResult",
    "PublicationForExecution",
    "PublicationIdempotencyStore",
    "PublicationPublisher",
]
