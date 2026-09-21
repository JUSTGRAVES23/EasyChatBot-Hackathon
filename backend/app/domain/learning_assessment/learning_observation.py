from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)


@dataclass(frozen=True, slots=True)
class LearningObservationCandidate:
    """Immutable, non-persistent observation proposed by a character analyzer.

    This is a proposal, not canonical learner state. The observation_id is the
    stable idempotency key supplied by the analysis boundary.
    """

    observation_id: str
    learner_id: str
    world_id: str
    skill_id: str
    category: LearningEvidenceCategory
    status: LearningEvidenceStatus
    severity: LearningEvidenceSeverity
    confidence: float
    subtype: str | None
    learner_text: str | None
    expected_text: str | None
    explanation: str | None
    source: LearningEvidenceSource
    observed_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("observation_id", self.observation_id),
            ("learner_id", self.learner_id),
            ("world_id", self.world_id),
            ("skill_id", self.skill_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")

        for name, value in (
            ("learner_text", self.learner_text),
            ("expected_text", self.expected_text),
            ("explanation", self.explanation),
            ("subtype", self.subtype),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{name} must not be blank when supplied.")
