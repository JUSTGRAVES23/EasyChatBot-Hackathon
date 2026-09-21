from datetime import datetime, timezone

from app.application.learning_assessment.character_learning_evidence_mapper import (
    CharacterLearningEvidenceMapper,
)
from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)
from app.domain.learning_assessment.learning_observation import (
    LearningObservationCandidate,
)


def test_mapper_preserves_observation_id_as_idempotency_key():
    candidate = LearningObservationCandidate(
        observation_id="turn-123:error-0",
        learner_id="learner-1",
        world_id="world-1",
        skill_id="grammar.past_tense",
        category=LearningEvidenceCategory.GRAMMAR,
        status=LearningEvidenceStatus.CONFIRMED_ERROR,
        severity=LearningEvidenceSeverity.MEDIUM,
        confidence=0.95,
        subtype="past_tense",
        learner_text="Hier je vais.",
        expected_text="Hier je suis allé.",
        explanation="Past tense mismatch.",
        source=LearningEvidenceSource.CHARACTER_CONVERSATION,
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    evidence = CharacterLearningEvidenceMapper.to_learning_evidence(candidate)

    assert evidence.observation_id == candidate.observation_id
    assert evidence.evidence_id == candidate.observation_id
    assert evidence.learner_id == candidate.learner_id
    assert evidence.skill_id == candidate.skill_id
