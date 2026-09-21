from __future__ import annotations

from app.domain.learning_assessment.learning_evidence import LearningEvidence
from app.domain.learning_assessment.learning_observation import (
    LearningObservationCandidate,
)


class CharacterLearningEvidenceMapper:
    """Pure mapping from an accepted observation candidate to LearningEvidence.

    This mapper has no repository, provider, clock or learner-state dependency.
    """

    @staticmethod
    def to_learning_evidence(
        candidate: LearningObservationCandidate,
    ) -> LearningEvidence:
        return LearningEvidence(
            evidence_id=candidate.observation_id,
            observation_id=candidate.observation_id,
            learner_id=candidate.learner_id,
            world_id=candidate.world_id,
            skill_id=candidate.skill_id,
            category=candidate.category,
            status=candidate.status,
            severity=candidate.severity,
            confidence=candidate.confidence,
            subtype=candidate.subtype,
            learner_text=candidate.learner_text,
            expected_text=candidate.expected_text,
            explanation=candidate.explanation,
            source=candidate.source,
            created_at=candidate.observed_at,
        )
