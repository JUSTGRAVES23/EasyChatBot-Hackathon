from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PrivacyEvidenceRecord:
    evidence_id: str
    activity_id: str
    evidence_type: str
    description: str
    source_system: str
    control_reference: str
    collected_at: datetime
    owner: str
    status: str
    legal_references: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
