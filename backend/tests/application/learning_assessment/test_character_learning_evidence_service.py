from datetime import datetime, timezone

import pytest

from app.application.learning_assessment.character_learning_evidence_service import (
    CharacterLearningEvidenceService,
)
from app.application.learning_assessment.learning_evidence_policy import (
    PermissiveLearningEvidenceWorldPolicy,
)
from app.application.learning_assessment.learner_skill_state_service import (
    LearnerSkillStateService,
)
from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)


class EvidenceRepo:
    def __init__(self):
        self.saved = []
        self.existing = None

    async def get_by_observation_id(self, observation_id):
        for evidence in self.saved:
            if evidence.observation_id == observation_id:
                return evidence

        return self.existing

    async def save(self, evidence):
        self.saved.append(evidence)
        return evidence

    async def get_recent_for_skill(self, **kwargs):
        return []


class SkillStateRepo:
    def __init__(self):
        self.states = {}

    def get(self, *, learner_id, world_id, skill_id):
        return self.states.get((learner_id, world_id, skill_id))

    def save(self, state):
        self.states[(state.learner_id, state.world_id, state.skill_id)] = state
        return state


def make_service():
    return CharacterLearningEvidenceService(
        evidence_repository=EvidenceRepo(),
        skill_state_repository=SkillStateRepo(),
        skill_state_service=LearnerSkillStateService(),
        world_policy=PermissiveLearningEvidenceWorldPolicy(),
    )


@pytest.mark.asyncio
async def test_confirmed_character_error_updates_reinforcement_state():
    service = make_service()

    result = await service.record(
        observation_id="obs-1",
        learner_id="learner-1",
        world_id="french",
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
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert result.evidence.status is LearningEvidenceStatus.CONFIRMED_ERROR
    assert result.state is not None
    assert result.state.incorrect_count == 1
    assert result.state.failure_streak == 1
    assert result.reinforcement_decision is not None
    assert result.reinforcement_decision.priority.value == "MEDIUM"


@pytest.mark.asyncio
async def test_uncertain_observation_is_retained_without_failure():
    service = make_service()

    result = await service.record(
        observation_id="obs-1",
        learner_id="learner-1",
        world_id="french",
        skill_id="register",
        category=LearningEvidenceCategory.REGISTER,
        status=LearningEvidenceStatus.UNCERTAIN,
        severity=LearningEvidenceSeverity.LOW,
        confidence=0.55,
        subtype="professional",
        learner_text="Salut, tu peux regarder ça ?",
        expected_text="Pourriez-vous regarder ceci ?",
        explanation="Potential register mismatch; context is insufficient.",
        source=LearningEvidenceSource.CHARACTER_CONVERSATION,
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert result.evidence.status is LearningEvidenceStatus.UNCERTAIN
    assert result.state is None
    assert result.reinforcement_decision is None


@pytest.mark.asyncio
async def test_repeated_character_errors_escalate():
    service = make_service()

    kwargs = dict(
        learner_id="learner-1",
        world_id="french",
        skill_id="expression.collocation",
        category=LearningEvidenceCategory.EXPRESSION,
        status=LearningEvidenceStatus.CONFIRMED_ERROR,
        severity=LearningEvidenceSeverity.MEDIUM,
        confidence=0.9,
        subtype="collocation",
        learner_text="faire une décision",
        expected_text="prendre une décision",
        explanation="Preferred collocation.",
        source=LearningEvidenceSource.CHARACTER_CONVERSATION,
    )

    first = await service.record(
        **kwargs,
        observation_id="obs-1",
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    second = await service.record(
        **kwargs,
        observation_id="obs-2",
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert first.reinforcement_decision.priority.value == "MEDIUM"
    assert second.reinforcement_decision.priority.value == "HIGH"
    assert second.state.failure_streak == 2


@pytest.mark.asyncio
async def test_retry_of_same_observation_is_idempotent():
    service = make_service()

    kwargs = dict(
        observation_id="same-observation",
        learner_id="learner-1",
        world_id="french",
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
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    first = await service.record(**kwargs)
    second = await service.record(**kwargs)

    assert first.evidence.evidence_id == second.evidence.evidence_id
    assert second.state is not None
    assert second.state.incorrect_count == 1
    assert second.state.failure_streak == 1

    # Idempotent retry must not apply reinforcement a second time.
    assert second.reinforcement_decision is None