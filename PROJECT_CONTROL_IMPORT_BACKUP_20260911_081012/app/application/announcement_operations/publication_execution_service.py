"""WS-22.3.1 publication execution application contract."""

from __future__ import annotations

from app.application.announcement_operations.publication_execution_ports import (
    PublicationAuditSink,
    PublicationExecutionRepository,
    PublicationIdempotencyStore,
    PublicationPublisher,
)
from app.domain.announcement_publication.execution import (
    PublishAnnouncementCommand,
    PublicationAuditEvent,
    PublicationExecutionErrorCode,
    PublicationExecutionResult,
)


class PublicationExecutionService:
    """Execute an approved publication through an injected publishing port.

    This service contains orchestration only. It does not know Telegram,
    HTTP, frontend concerns, credentials, or provider-specific APIs.
    """

    def __init__(
        self,
        *,
        repository: PublicationExecutionRepository,
        publisher: PublicationPublisher,
        idempotency_store: PublicationIdempotencyStore,
        audit_sink: PublicationAuditSink,
    ) -> None:
        if any(
            dependency is None
            for dependency in (
                repository,
                publisher,
                idempotency_store,
                audit_sink,
            )
        ):
            raise ValueError("All publication execution dependencies are required.")

        self._repository = repository
        self._publisher = publisher
        self._idempotency_store = idempotency_store
        self._audit_sink = audit_sink

    async def execute(
        self,
        command: PublishAnnouncementCommand,
    ) -> PublicationExecutionResult:
        """Execute one explicit publication request."""

        existing = await self._idempotency_store.get_result(
            command.idempotency_key
        )
        if existing is not None:
            return existing

        publication = await self._repository.get_for_execution(
            command.publication_id
        )

        if publication is None:
            result = PublicationExecutionResult.failed(
                publication_id=command.publication_id,
                idempotency_key=command.idempotency_key,
                error_code=PublicationExecutionErrorCode.INVALID_STATE,
                error_message="Publication is not available for execution.",
            )
            await self._record_result(command, result)
            return result

        if publication.status.lower() not in {"approved", "ready_to_publish"}:
            result = PublicationExecutionResult.failed(
                publication_id=command.publication_id,
                idempotency_key=command.idempotency_key,
                error_code=PublicationExecutionErrorCode.INVALID_STATE,
                error_message="Publication is not in an executable state.",
            )
            await self._record_result(command, result)
            return result

        try:
            provider_reference = await self._publisher.publish(
                publication=publication,
                idempotency_key=command.idempotency_key,
            )
        except Exception as exc:  # noqa: BLE001
            result = PublicationExecutionResult.failed(
                publication_id=command.publication_id,
                idempotency_key=command.idempotency_key,
                error_code=PublicationExecutionErrorCode.PROVIDER_ERROR,
                error_message=str(exc) or "Publication provider failed.",
            )
            await self._record_result(command, result)
            return result

        result = PublicationExecutionResult.succeeded(
            publication_id=command.publication_id,
            idempotency_key=command.idempotency_key,
            provider_reference=provider_reference,
        )
        await self._record_result(command, result)
        return result

    async def _record_result(
        self,
        command: PublishAnnouncementCommand,
        result: PublicationExecutionResult,
    ) -> None:
        await self._idempotency_store.store_result(result)
        await self._repository.record_execution(result)

        await self._audit_sink.record(
            PublicationAuditEvent(
                event_name="announcement_publication_execution",
                publication_id=result.publication_id,
                requested_by=command.requested_by,
                status=result.status,
                occurred_at=result.executed_at,
                idempotency_key=result.idempotency_key,
                provider_reference=result.provider_reference,
                error_code=result.error_code,
                safe_metadata={"execution_status": result.status.value},
            )
        )


__all__ = ["PublicationExecutionService"]

