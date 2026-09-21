from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LearningEvidenceCategory(str, Enum):
    PRONUNCIATION = "PRONUNCIATION"
    GRAMMAR = "GRAMMAR"
    EXPRESSION = "EXPRESSION"
    REGISTER = "REGISTER"


class LearningEvidenceStatus(str, Enum):
    CONFIRMED_ERROR = "CONFIRMED_ERROR"
    UNCERTAIN = "UNCERTAIN"
    DISMISSED = "DISMISSED"


class LearningEvidenceSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LearningEvidenceSource(str, Enum):
    CHARACTER_CONVERSATION = "CHARACTER_CONVERSATION"


@dataclass(frozen=True, slots=True)
class LearningEvidence:
    """Normalized educational evidence from a controlled analysis boundary.

    ``observation_id`` is the upstream idempotency key. A retry of the same
    character/voice observation must not create a second learner failure.
    ``skill_id`` and ``subtype`` are interpreted by the selected World.
    """

    evidence_id: str
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
    created_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("evidence_id", self.evidence_id),
            ("observation_id", self.observation_id),
            ("learner_id", self.learner_id),
            ("world_id", self.world_id),
            ("skill_id", self.skill_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")

        if not isinstance(self.category, LearningEvidenceCategory):
            raise ValueError("category must be a LearningEvidenceCategory.")
        if not isinstance(self.status, LearningEvidenceStatus):
            raise ValueError("status must be a LearningEvidenceStatus.")
        if not isinstance(self.severity, LearningEvidenceSeverity):
            raise ValueError("severity must be a LearningEvidenceSeverity.")

        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence, (int, float)
        ):
            raise ValueError("confidence must be numeric.")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")

        for name, value in (
            ("subtype", self.subtype),
            ("learner_text", self.learner_text),
            ("expected_text", self.expected_text),
            ("explanation", self.explanation),
        ):
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be a non-empty string or None.")

        if not isinstance(self.source, LearningEvidenceSource):
            raise ValueError("source must be a LearningEvidenceSource.")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime.")
