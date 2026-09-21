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
from app.domain.learning_assessment.learner_error_candidate import (
    LearnerErrorCandidate,
)


def make_observation(**overrides):
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


def test_learner_error_candidate_requires_learner_text():
    observation = make_observation()

    assert LearnerErrorCandidate(observation=observation).observation == observation

    with pytest.raises(ValueError):
        LearnerErrorCandidate(
            observation=make_observation(learner_text=None)
        )
