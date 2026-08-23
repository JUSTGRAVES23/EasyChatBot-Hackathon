from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProcessingActivityRecord:
    """ROPA-oriented processing activity record.

    Governance/documentation only. It does not execute processing.
    """

    activity_id: str
    name: str
    purpose: str
    controller_role: str
    data_subjects: tuple[str, ...]
    data_categories: tuple[str, ...]
    special_category_data: bool
    recipients: tuple[str, ...]
    processors: tuple[str, ...]
    systems: tuple[str, ...]
    transfer_status: str
    retention_rule: str
    security_measures: tuple[str, ...]
    lawful_basis: str
    legal_references: tuple[str, ...]
    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
