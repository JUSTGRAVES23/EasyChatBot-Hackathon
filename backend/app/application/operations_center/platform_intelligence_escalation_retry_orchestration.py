"""Contracts for controlled PI escalation retry orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.application.operations_center.platform_intelligence_escalation_dispatch import (
    PlatformIntelligenceEscalationDispatchRequest,
)


class PlatformIntelligenceRetryRunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceRetryState:
    """Authoritative state required immediately before retry dispatch."""

    notification_key: str
    recommendation_id: str
    recommendation_status: str
    review_status: str
    decision_status: str
    quality_gate_status: str
    dispatch_request: PlatformIntelligenceEscalationDispatchRequest
    email_request: Any

    def __post_init__(self) -> None:
        for field_name in (
            "notification_key",
            "recommendation_id",
            "recommendation_status",
            "review_status",
            "decision_status",
            "quality_gate_status",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be nonblank.")

        if self.dispatch_request.notification_key != self.notification_key:
            raise ValueError(
                "dispatch_request.notification_key must match notification_key."
            )
        if self.dispatch_request.recommendation_id != self.recommendation_id:
            raise ValueError(
                "dispatch_request.recommendation_id must match recommendation_id."
            )


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceRetryRunResult:
    notification_key: str
    status: PlatformIntelligenceRetryRunStatus
    reason: str
    attempt: int | None = None
    provider_message_id: str | None = None

    def __post_init__(self) -> None:
        if not self.notification_key.strip():
            raise ValueError("notification_key must be nonblank.")
        if not self.reason.strip():
            raise ValueError("reason must be nonblank.")
        if self.attempt is not None and self.attempt < 1:
            raise ValueError("attempt must be at least 1.")
