from datetime import datetime, timezone

import pytest

from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)
from app.domain.learning_assessment.learning_observation import (
    LearningObservationCandidate,
)


def make_candidate(**overrides):
    values = {
        "observation_id": "obs-1",
        "learner_id": "learner-1",
        "world_id": "world-1",
        "skill_id": "skill-1",
        "category": LearningEvidenceCategory.GRAMMAR,
        "status": LearningEvidenceStatus.CONFIRMED_ERROR,
        "severity": LearningEvidenceSeverity.MEDIUM,
        "confidence": 0.9,
        "subtype": "verb_tense",
        "learner_text": "I have went.",
        "expected_text": "I have gone.",
        "explanation": "Use the past participle after have.",
        "source": LearningEvidenceSource.CHARACTER_CONVERSATION,
        "observed_at": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return LearningObservationCandidate(**values)


def test_candidate_is_immutable_and_validates_confidence():
    candidate = make_candidate()

    with pytest.raises((AttributeError, TypeError)):
        candidate.confidence = 0.5  # type: ignore[misc]

    with pytest.raises(ValueError):
        make_candidate(confidence=1.1)


def test_candidate_rejects_blank_identity():
    with pytest.raises(ValueError):
        make_candidate(skill_id="   ")


def test_candidate_rejects_blank_learner_text_when_supplied():
    with pytest.raises(ValueError):
        make_candidate(learner_text="   ")
