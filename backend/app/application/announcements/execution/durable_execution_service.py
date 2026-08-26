"""WS-22.3.2 durable execution orchestration."""

from __future__ import annotations

from backend.app.application.announcements.execution.contracts import (
    AnnouncementPublisher,
    PublicationExecutionRequest,
    PublicationExecutionResult,
    PublicationExecutionStatus,
)
from backend.app.application.announcements.execution.durable_contracts import (
    DurableExecutionStatus,
    PublicationExecutionRepository,
)


class DurablePublicationExecutionService:
    """Retry-safe execution service backed by durable idempotency state.

    A completed idempotency key is never sent again.

    A STARTED record is treated as an interrupted attempt and is retryable.

    A FAILED record is also retryable. Before a retry is executed, the
    repository is responsible for incrementing the durable attempt counter
    and transitioning the record back to STARTED.

    The repository implementation must make creation atomic against a
    unique idempotency key.
    """

    def __init__(
        self,
        *,
        publisher: AnnouncementPublisher,
        execution_repository: PublicationExecutionRepository,
        audit,
    ) -> None:
        if publisher is None:
            raise ValueError("publisher cannot be None.")

        if execution_repository is None:
            raise ValueError("execution_repository cannot be None.")

        if audit is None:
            raise ValueError("audit cannot be None.")

        self._publisher = publisher
        self._repository = execution_repository
        self._audit = audit

    async def execute(
        self,
        *,
        publication,
        request: PublicationExecutionRequest,
    ) -> PublicationExecutionResult:
        existing = await self._repository.get_by_idempotency_key(
            request.idempotency_key
        )

        # A successful execution is terminal for the idempotency key.
        # Never call the external provider again.
        if (
            existing is not None
            and existing.status is DurableExecutionStatus.SUCCEEDED
        ):
            return PublicationExecutionResult(
                publication_id=existing.publication_id,
                status=PublicationExecutionStatus.IDEMPOTENT_REPLAY,
                idempotency_key=existing.idempotency_key,
                correlation_id=request.correlation_id,
                provider_message_id=existing.provider_message_id,
            )

        self._assert_approved(publication)

        # The repository owns the atomic unique-key operation. If another
        # worker already created the same key, re-read and honour its state.
        if existing is None:
            try:
                record = await self._repository.create_started(
                    publication_id=publication.id,
                    idempotency_key=request.idempotency_key,
                    correlation_id=request.correlation_id,
                )
            except Exception:
                record = await self._repository.get_by_idempotency_key(
                    request.idempotency_key
                )

                if record is None:
                    raise

        elif existing.status is DurableExecutionStatus.FAILED:
            # A FAILED execution is retryable. Reuse the same durable
            # idempotency record and increment its attempt number rather
            # than creating a second row.
            record = await self._repository.start_retry(
                idempotency_key=request.idempotency_key,
            )

        else:
            # STARTED represents an interrupted/incomplete attempt.
            # Preserve the existing durable attempt number and retry it.
            record = existing

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

            await self._repository.mark_failed(
                idempotency_key=request.idempotency_key,
                error_code=error_code,
            )

            await self._audit.record_failure(
                publication_id=publication.id,
                actor=request.actor,
                correlation_id=request.correlation_id,
                error_code=error_code,
            )

            return PublicationExecutionResult(
                publication_id=publication.id,
                status=PublicationExecutionStatus.FAILED,
                idempotency_key=request.idempotency_key,
                correlation_id=request.correlation_id,
                error_code=error_code,
            )

        publication.publish_success(provider_message_id)

        await self._repository.mark_succeeded(
            idempotency_key=request.idempotency_key,
            provider_message_id=provider_message_id,
        )

        await self._audit.record_success(
            publication_id=publication.id,
            actor=request.actor,
            correlation_id=request.correlation_id,
            provider_message_id=provider_message_id,
        )

        return PublicationExecutionResult(
            publication_id=publication.id,
            status=PublicationExecutionStatus.SUCCEEDED,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            provider_message_id=provider_message_id,
        )

    @staticmethod
    def _assert_approved(publication) -> None:
        value = getattr(publication.status, "value", publication.status)

        if value != "approved":
            raise ValueError(
                "Only approved publications may be executed."
            )

    @staticmethod
    def _error_code(exc: Exception) -> str:
        explicit = getattr(exc, "error_code", None)

        return (
            explicit.strip()[:100]
            if isinstance(explicit, str) and explicit.strip()
            else type(exc).__name__.upper()[:100]
        )