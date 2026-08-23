from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PrivacyChangeStatus(str, Enum):
    DRAFT = "draft"
    ASSESSED = "assessed"
    PENDING_DPO_GRC = "pending_dpo_grc"
    APPROVED = "approved"
    BLOCKED = "blocked"


class PrivacyChangeRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class PrivacyChange:
    """A controlled record for a potentially privacy-impacting change."""

    change_id: str
    title: str
    description: str
    affected_processing_ids: list[str] = field(default_factory=list)
    affected_data_map_ids: list[str] = field(default_factory=list)
    data_categories_changed: bool = False
    purpose_changed: bool = False
    recipients_changed: bool = False
    retention_changed: bool = False
    processor_changed: bool = False
    transfer_changed: bool = False
    automated_decision_changed: bool = False
    dpia_screening_required: bool = False
    risk: PrivacyChangeRisk = PrivacyChangeRisk.LOW
    status: PrivacyChangeStatus = PrivacyChangeStatus.DRAFT
    dpo_required: bool = False
    grc_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
