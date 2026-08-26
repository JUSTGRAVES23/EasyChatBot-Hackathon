"""WS-22.3.1 provider/channel-independent publication execution domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Mapping


class PublicationExecutionStatus(StrEnum):
    """Terminal/observable execution outcomes."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ALREADY_PUBLISHED = "already_published"


class PublicationExecutionErrorCode(StrEnum):
    """Stable application error categories."""

    INVALID_STATE = "invalid_state"
    DESTINATION_NOT_CONFIGURED = "destination_not_configured"
    PROVIDER_ERROR = "provider_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PublishAnnouncementCommand:
    """Explicit request to publish one approved publication."""

    publication_id: str
    idempotency_key: str
    requested_by: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("publication_id", self.publication_id),
            ("idempotency_key", self.idempotency_key),
            ("requested_by", self.requested_by),
        ):
            if not value or not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")


@dataclass(frozen=True, slots=True)
class PublicationExecutionResult:
    """Safe result returned by the execution use case."""

    status: PublicationExecutionStatus
    publication_id: str
    idempotency_key: str
    executed_at: datetime
    provider_reference: str | None = None
    error_code: PublicationExecutionErrorCode | None = None
    error_message: str | None = None

    @classmethod
    def succeeded(
        cls,
        *,
        publication_id: str,
        idempotency_key: str,
        provider_reference: str | None = None,
    ) -> "PublicationExecutionResult":
        return cls(
            status=PublicationExecutionStatus.SUCCEEDED,
            publication_id=publication_id,
            idempotency_key=idempotency_key,
            executed_at=datetime.now(timezone.utc),
            provider_reference=provider_reference,
        )

    @classmethod
    def already_published(
        cls,
        *,
        publication_id: str,
        idempotency_key: str,
        provider_reference: str | None = None,
    ) -> "PublicationExecutionResult":
        return cls(
            status=PublicationExecutionStatus.ALREADY_PUBLISHED,
            publication_id=publication_id,
            idempotency_key=idempotency_key,
            executed_at=datetime.now(timezone.utc),
            provider_reference=provider_reference,
        )

    @classmethod
    def failed(
        cls,
        *,
        publication_id: str,
        idempotency_key: str,
        error_code: PublicationExecutionErrorCode,
        error_message: str,
    ) -> "PublicationExecutionResult":
        if not error_message.strip():
            raise ValueError("error_message cannot be empty.")

        return cls(
            status=PublicationExecutionStatus.FAILED,
            publication_id=publication_id,
            idempotency_key=idempotency_key,
            executed_at=datetime.now(timezone.utc),
            error_code=error_code,
            error_message=error_message,
        )


@dataclass(frozen=True, slots=True)
class PublicationAuditEvent:
    """Audit record contract; never contains publication body or secrets."""

    event_name: str
    publication_id: str
    requested_by: str
    status: PublicationExecutionStatus
    occurred_at: datetime
    idempotency_key: str
    provider_reference: str | None = None
    error_code: PublicationExecutionErrorCode | None = None
    safe_metadata: Mapping[str, str] | None = None


__all__ = [
    "PublicationAuditEvent",
    "PublicationExecutionErrorCode",
    "PublicationExecutionResult",
    "PublicationExecutionStatus",
    "PublishAnnouncementCommand",
]
