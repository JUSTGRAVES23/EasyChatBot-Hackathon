from __future__ import annotations

from .privacy_change import PrivacyChange
from .privacy_governance_composition import (
    get_privacy_governance_composition,
)
from .privacy_governance_flow_service import PrivacyGovernanceFlowResult


def process_new_processing_governance(
    change: PrivacyChange,
    *,
    automated_validation_passed: bool,
    case_id: str | None = None,
    trigger_source: str = "Processing Registry",
    processing_ids: tuple[str, ...] = (),
    data_map_ids: tuple[str, ...] = (),
) -> PrivacyGovernanceFlowResult:
    """Runtime bridge for existing privacy processing integrations.

    Existing privacy processing should call this function after it has a
    deterministic validation result. The function uses the same composition
    instance observed by the Operations Center API.

    No HTTP request is required and no approval decision is made here.
    """

    composition = get_privacy_governance_composition()

    return composition.flow_service.process_new_processing(
        change,
        automated_validation_passed=automated_validation_passed,
        case_id=case_id,
        trigger_source=trigger_source,
        processing_ids=processing_ids,
        data_map_ids=data_map_ids,
    )
