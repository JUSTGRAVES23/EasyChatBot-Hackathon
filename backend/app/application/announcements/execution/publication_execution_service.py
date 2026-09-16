"""WS-22.3.1 provider-independent publication execution service."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.application.announcements.execution.contracts import (
    AnnouncementPublisher,
    PublicationExecutionRequest,
    PublicationExecutionResult,
    PublicationExecutionStatus,
)


class ExecutablePublication(Protocol):
    """Minimum aggregate surface required by the execution service."""

    id: UUID
    title: str
    content: str
    status: object

    def begin_publish(self) -> None: ...

    def publish_success(self, provider_message_id: str | None = None) -> None: ...

    def mark_failure(self, reason: str) -> None: ...


class PublicationExecutionAudit(Protocol):
    """Minimal audit boundary used by execution.

    The concrete publication-event repository remains an existing
    application concern; this protocol prevents execution from coupling to
    a particular persistence implementation.
    """

    async def record_success(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        provider_message_id: str | None,
    ) -> None: ...

    async def record_failure(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        error_code: str,
    ) -> None: ...


class PublicationExecutionService:
    """Execute approved publications through a provider-independent port.

    The service owns orchestration and idempotency. It does not know which
    channel/provider performs the external publication.
    """

    def __init__(
        self,
        *,
        publisher: AnnouncementPublisher,
        audit: PublicationExecutionAudit,
    ) -> None:
        if publisher is None:
            raise ValueError("publisher cannot be None.")
        if audit is None:
            raise ValueError("audit cannot be None.")
        self._publisher = publisher
        self._audit = audit
        self._completed: dict[str, PublicationExecutionResult] = {}

    async def execute(
        self,
        *,
        publication: ExecutablePublication,
        request: PublicationExecutionRequest,
    ) -> PublicationExecutionResult:
        if publication is None:
            raise ValueError("publication cannot be None.")

        existing = self._completed.get(request.idempotency_key)
        if existing is not None:
            return PublicationExecutionResult(
                publication_id=existing.publication_id,
                status=PublicationExecutionStatus.IDEMPOTENT_REPLAY,
                idempotency_key=existing.idempotency_key,
                correlation_id=request.correlation_id,
                provider_message_id=existing.provider_message_id,
                error_code=existing.error_code,
                error_message=existing.error_message,
            )

        self._assert_approved(publication)
        publication.begin_publish()

        try:
            provider_message_id = await self._publisher.publish(
                publication_id=publication.id,
                title=publication.title,
                content=publication.content,
                correlation_id=request.correlation_id,
                idempotency_key=request.idempotency_key,
            )
        except Exception as exc:
            error_code = self._error_code(exc)
            publication.mark_failure(error_code)
            await self._audit.record_failure(
                publication_id=publication.id,
                actor=request.actor,
                correlation_id=request.correlation_id,
                error_code=error_code,
            )
            result = PublicationExecutionResult(
                publication_id=publication.id,
                status=PublicationExecutionStatus.FAILED,
                idempotency_key=request.idempotency_key,
                correlation_id=request.correlation_id,
                error_code=error_code,
            )
            return result

        publication.publish_success(provider_message_id)
        await self._audit.record_success(
            publication_id=publication.id,
            actor=request.actor,
            correlation_id=request.correlation_id,
            provider_message_id=provider_message_id,
        )

        result = PublicationExecutionResult(
            publication_id=publication.id,
            status=PublicationExecutionStatus.SUCCEEDED,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            provider_message_id=provider_message_id,
        )
        self._completed[request.idempotency_key] = result
        return result

    @staticmethod
    def _assert_approved(publication: ExecutablePublication) -> None:
        status_value = getattr(publication.status, "value", publication.status)
        if status_value != "approved":
            raise ValueError(
                "Only approved publications may be executed."
            )

    @staticmethod
    def _error_code(exc: Exception) -> str:
        """Return a stable, non-sensitive operational error code."""
        explicit = getattr(exc, "error_code", None)
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()[:100]
        return type(exc).__name__.upper()[:100]

