"""Contracts for the bounded PI escalation retry worker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PlatformIntelligenceRetryWorkerItemStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceRetryWorkerItemResult:
    notification_key: str
    status: PlatformIntelligenceRetryWorkerItemStatus
    reason: str
    attempt: int | None = None
    provider_message_id: str | None = None
    error_type: str | None = None

    def __post_init__(self) -> None:
        if not self.notification_key.strip():
            raise ValueError("notification_key must be nonblank.")
        if not self.reason.strip():
            raise ValueError("reason must be nonblank.")
        if self.attempt is not None and self.attempt < 1:
            raise ValueError("attempt must be at least 1.")
        if self.error_type is not None and not self.error_type.strip():
            raise ValueError("error_type must be nonblank when provided.")


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceRetryWorkerResult:
    requested_limit: int
    discovered_count: int
    processed_count: int
    succeeded_count: int
    skipped_count: int
    failed_count: int
    items: tuple[PlatformIntelligenceRetryWorkerItemResult, ...]

    def __post_init__(self) -> None:
        if self.requested_limit < 1:
            raise ValueError("requested_limit must be at least 1.")
        if self.discovered_count < 0:
            raise ValueError("discovered_count cannot be negative.")
        if self.processed_count < 0:
            raise ValueError("processed_count cannot be negative.")
        if self.processed_count != len(self.items):
            raise ValueError("processed_count must equal the number of items.")
        if self.succeeded_count < 0 or self.skipped_count < 0 or self.failed_count < 0:
            raise ValueError("result counts cannot be negative.")
        if (
            self.succeeded_count + self.skipped_count + self.failed_count
            != self.processed_count
        ):
            raise ValueError("result counts must equal processed_count.")
        if self.discovered_count > self.requested_limit:
            raise ValueError("discovered_count cannot exceed requested_limit.")
        keys = [item.notification_key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("worker result cannot contain duplicate notification keys.")


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceRetryWorkerRequest:
    limit: int = 100

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("limit must be at least 1.")
