from datetime import datetime, timezone

import pytest

from app.domain.learning_assessment.learning_evidence import (
    LearningEvidence,
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)


def make_evidence(**overrides):
    values = dict(
        evidence_id="e1",
        observation_id="obs-1",
        learner_id="learner-1",
        world_id="french",
        skill_id="grammar.past_tense",
        category=LearningEvidenceCategory.GRAMMAR,
        status=LearningEvidenceStatus.CONFIRMED_ERROR,
        severity=LearningEvidenceSeverity.MEDIUM,
        confidence=0.95,
        subtype="past_tense",
        learner_text="Hier je vais au marché.",
        expected_text="Hier je suis allé au marché.",
        explanation="Past tense mismatch.",
        source=LearningEvidenceSource.CHARACTER_CONVERSATION,
        created_at=datetime.now(timezone.utc),
    )
    values.update(overrides)
    return LearningEvidence(**values)


def test_learning_evidence_accepts_world_specific_evidence():
    evidence = make_evidence()

    assert evidence.world_id == "french"
    assert evidence.category is LearningEvidenceCategory.GRAMMAR
    assert evidence.status is LearningEvidenceStatus.CONFIRMED_ERROR
    assert evidence.confidence == 0.95


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_learning_evidence_rejects_invalid_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        make_evidence(confidence=confidence)


def test_learning_evidence_rejects_empty_skill():
    with pytest.raises(ValueError, match="skill_id"):
        make_evidence(skill_id=" ")
