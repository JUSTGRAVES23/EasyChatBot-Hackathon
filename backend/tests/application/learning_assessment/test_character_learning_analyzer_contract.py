from datetime import datetime, timezone

import pytest

from app.application.learning_assessment.character_learning_analyzer import (
    CharacterLearningAnalysis,
)
from app.application.learning_assessment.character_learning_observation_policy import (
    CharacterLearningObservationPolicy,
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
from app.domain.learning_assessment.learner_error_candidate import (
    LearnerErrorCandidate,
)


class DeterministicWorldSkillPolicy:
    """Test-only World/Skill governance double."""

    def __init__(self):
        self.calls = []

    async def validate(self, *, world_id: str, skill_id: str):
        self.calls.append((world_id, skill_id))


def candidate(observation_id: str, confidence: float = 0.9):
    return LearningObservationCandidate(
        observation_id=observation_id,
        learner_id="learner-1",
        world_id="world-1",
        skill_id="skill-1",
        category=LearningEvidenceCategory.GRAMMAR,
        status=LearningEvidenceStatus.CONFIRMED_ERROR,
        severity=LearningEvidenceSeverity.MEDIUM,
        confidence=confidence,
        subtype="verb_tense",
        learner_text="I have went.",
        expected_text="I have gone.",
        explanation="Past participle required.",
        source=LearningEvidenceSource.CHARACTER_CONVERSATION,
        observed_at=datetime.now(timezone.utc),
    )


def test_analysis_requires_errors_to_reference_observations():
    observation = candidate("obs-1")
    unrelated = candidate("obs-2")

    with pytest.raises(ValueError):
        CharacterLearningAnalysis(
            observations=(observation,),
            learner_errors=(
                LearnerErrorCandidate(observation=unrelated),
            ),
        )


@pytest.mark.asyncio
async def test_policy_rejects_low_confidence_candidates():
    world_policy = DeterministicWorldSkillPolicy()

    policy = CharacterLearningObservationPolicy(
        world_policy=world_policy,
        minimum_confidence=0.8,
    )

    accepted = await policy.validate(
        (candidate("obs-1", 0.9), candidate("obs-2", 0.7))
    )

    assert [item.observation_id for item in accepted] == ["obs-1"]
    assert world_policy.calls == [("world-1", "skill-1")]


@pytest.mark.asyncio
async def test_policy_limits_candidates_per_turn():
    world_policy = DeterministicWorldSkillPolicy()

    policy = CharacterLearningObservationPolicy(
        world_policy=world_policy,
        maximum_candidates_per_turn=1,
    )

    with pytest.raises(ValueError):
        await policy.validate(
            (candidate("obs-1"), candidate("obs-2"))
        )
