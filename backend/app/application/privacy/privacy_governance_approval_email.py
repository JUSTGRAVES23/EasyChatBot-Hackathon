@dataclass(frozen=True, slots=True)
class PrivacyGovernanceApprovalEmailSnapshot:
    case_id: str
    change_id: str
    assessment_type: str
    title: str
    summary: str
    risk: str
    validation_status: str
    governance_status: str
    required_reviewers: tuple[str, ...]
    processing_ids: tuple[str, ...]
    data_map_ids: tuple[str, ...]
    review_url: str