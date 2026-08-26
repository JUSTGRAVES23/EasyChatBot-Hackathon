from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionResult,
)
from backend.app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)
from backend.app.domain.announcements.publication import Publication


@dataclass(frozen=True, slots=True)
class ApprovedPublicationExecutionService:
    """Application boundary from WS-23 approved state into WS-22."""

    durable_execution: DurablePublicationExecutionService

    def __post_init__(self) -> None:
        if self.durable_execution is None:
            raise ValueError("durable_execution cannot be None.")

    async def execute(
        self,
        *,
        publication: Publication,
        actor: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> PublicationExecutionResult:
        """Delegate an approved publication to the existing WS-22 service.

        WS-22 remains responsible for:
        - durable execution;
        - idempotency;
        - execution persistence;
        - execution audit;
        - retry semantics;
        - controlled provider invocation.
        """

        if publication is None:
            raise ValueError("publication cannot be None.")

        if not actor.strip():
            raise ValueError("actor cannot be empty.")

        if not idempotency_key.strip():
            raise ValueError("idempotency_key cannot be empty.")

        if not correlation_id.strip():
            raise ValueError("correlation_id cannot be empty.")

        try:
            publication_uuid = UUID(publication.publication_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                "Approved publication ID must be a UUID for WS-22 durable execution."
            ) from exc

        request = PublicationExecutionRequest(
            publication_id=publication_uuid,
            idempotency_key=idempotency_key.strip(),
            correlation_id=correlation_id.strip(),
            actor=actor.strip(),
        )

        return await self.durable_execution.execute(
            publication=_PublicationExecutionAdapter(publication),
            request=request,
        )


class _PublicationExecutionAdapter:
    """Adapt the WS-23 publication to the existing WS-22 execution contract."""

    def __init__(self, publication: Publication) -> None:
        self._publication = publication

    @property
    def id(self) -> UUID:
        return UUID(self._publication.publication_id)

    @property
    def title(self) -> str:
        return self._publication.title

    @property
    def content(self) -> str:
        return self._publication.content

    @property
    def status(self):
        return self._publication.status

    def begin_publish(self) -> None:
        self._publication.begin_publish()

    def mark_failure(self, reason: str) -> None:
        self._publication.mark_failure(reason)

    def publish_success(self, provider_message_id: str | None = None) -> None:
        del provider_message_id
        self._publication.publish_success()


__all__ = ["ApprovedPublicationExecutionService"]