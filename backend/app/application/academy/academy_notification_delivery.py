from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class AcademyDeliveryStatus(StrEnum):
    PENDING = "PENDING"
    SENDING = "SENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class AcademyEligibleUser:
    user_id: UUID
    email: str
    username: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AcademyDeliveryRecord:
    user_id: UUID
    notification_type: str
    status: AcademyDeliveryStatus
    attempt_count: int
    provider_message_id: str | None = None
    last_error: str | None = None


class AcademyUserQuery(Protocol):
    async def list_one_week_candidates(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[AcademyEligibleUser]:
        ...


class AcademyDeliveryRepository(Protocol):
    async def claim(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        now: datetime,
    ) -> AcademyDeliveryRecord | None:
        ...

    async def mark_succeeded(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        provider_message_id: str | None,
        now: datetime,
    ) -> None:
        ...

    async def mark_failed(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        error: str,
        now: datetime,
    ) -> None:
        ...
