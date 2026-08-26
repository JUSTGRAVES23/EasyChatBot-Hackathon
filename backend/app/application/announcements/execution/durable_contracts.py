"""WS-22.3.2 durable execution contracts.

The application layer depends on these contracts, not on SQLAlchemy or a
specific database. Infrastructure supplies the durable repository.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class DurableExecutionStatus(str, Enum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PublicationExecutionRecord:
    publication_id: UUID
    idempotency_key: str
    correlation_id: str
    attempt: int
    status: DurableExecutionStatus
    provider_message_id: str | None = None
    error_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PublicationExecutionRepository:
    """Port for durable execution state.

    Implementations must persist records transactionally using the
    application's existing persistence/session infrastructure.
    """

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> PublicationExecutionRecord | None:
        raise NotImplementedError

    async def create_started(
        self,
        *,
        publication_id: UUID,
        idempotency_key: str,
        correlation_id: str,
    ) -> PublicationExecutionRecord:
        raise NotImplementedError

    async def mark_succeeded(
        self,
        *,
        idempotency_key: str,
        provider_message_id: str | None,
    ) -> PublicationExecutionRecord:
        raise NotImplementedError

    async def mark_failed(
        self,
        *,
        idempotency_key: str,
        error_code: str,
    ) -> PublicationExecutionRecord:
        raise NotImplementedError
