from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProcessingActivity:
    """Machine-readable Beta 1 processing activity definition."""

    processing_id: str
    name: str
    purpose: str
    data_categories: tuple[str, ...]
    data_subjects: tuple[str, ...]
    source: tuple[str, ...]
    destinations: tuple[str, ...]
    legal_basis: str
    retention_id: str
    processor_ids: tuple[str, ...] = ()
    data_map_id: str = ""
    dpia_screening_id: str = ""
    gdpr_references: tuple[str, ...] = ()
    security_controls: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    approval_status: str = "PENDING"
