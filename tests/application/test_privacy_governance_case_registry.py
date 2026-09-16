from datetime import datetime, timezone

from app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)


def test_case_registry_supports_clickable_case_lookup():
    case = PrivacyGovernanceCase(
        case_id="PCR-001",
        title="New learner memory",
        summary="New memory processing introduced.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
    )
    registry = PrivacyGovernanceCaseRegistry([case])

    assert registry.get("PCR-001").summary == "New memory processing introduced."
    assert registry.pending()[0].case_id == "PCR-001"

