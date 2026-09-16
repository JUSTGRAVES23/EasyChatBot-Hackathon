from dataclasses import dataclass
from enum import StrEnum


class AssessmentOutcome(StrEnum):
    REQUIRED = "REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"
    LEGAL_REVIEW_REQUIRED = "LEGAL_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class ScreeningCriterion:
    code: str
    label: str
    satisfied: bool
    source: str
    source_version: str
    rationale: str


@dataclass(frozen=True, slots=True)
class ScreeningResult:
    screening_id: str
    processing_id: str
    status: str
    outcomes: tuple[dict, ...]
    reassessment_required: bool
    provenance: tuple[ScreeningCriterion, ...]
    rationale: str
