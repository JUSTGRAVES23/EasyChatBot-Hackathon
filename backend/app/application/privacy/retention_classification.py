from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetentionClassification:
    classification_id: str
    data_domain: str
    record_type: str
    retention_period: str
    trigger: str
    review_action: str
    deletion_action: str
    legal_policy_reference: str
    owner: str
    status: str = "DRAFT"
