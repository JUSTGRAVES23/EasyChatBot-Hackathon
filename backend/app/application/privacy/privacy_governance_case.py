from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PrivacyTriggerType(StrEnum):
    NEW_PROCESSING = "NEW_PROCESSING"
    PROCESSING_CHANGE = "PROCESSING_CHANGE"
    DATA_MAPPING_CHANGE = "DATA_MAPPING_CHANGE"
    RETENTION_CHANGE = "RETENTION_CHANGE"
    PROCESSOR_CHANGE = "PROCESSOR_CHANGE"
    DPIA_CHANGE = "DPIA_CHANGE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True, slots=True)
class PrivacyGovernanceCase:
    """Case-centric governance record rendered by the Operations Center.

    ``change_id`` is the stable link to the authoritative PrivacyChange.
    It is optional at model level for backward compatibility with older Beta
    fixtures; newly created runtime cases should always populate it.
    """

    case_id: str
    title: str
    summary: str
    trigger_type: PrivacyTriggerType
    triggered_at: datetime
    trigger_source: str
    change_id: str | None = None
    processing_ids: tuple[str, ...] = ()
    data_map_ids: tuple[str, ...] = ()
    risk: str = "MEDIUM"
    validation_status: str = "PENDING"
    email_status: str = "NOT_SENT"
    governance_status: str = "PENDING_DPO_GRC"
    final_decision: str | None = None
    final_decision_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("case_id", "title", "summary", "trigger_source"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} is required.")
        if self.change_id is not None and not self.change_id.strip():
            raise ValueError("change_id cannot be blank when provided.")
        if self.triggered_at.tzinfo is None:
            raise ValueError("triggered_at must be timezone-aware.")
        if self.final_decision_at is not None and self.final_decision_at.tzinfo is None:
            raise ValueError("final_decision_at must be timezone-aware.")
