from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.application.learning_assessment.character_learning_turn_service import (
    CharacterLearningTurnService,
)


@dataclass
class FakeObservation:
    observation_id: str
    category: object
    status: object
    severity: object
    confidence: float
    subtype: str | None = None
    learner_text: str | None = None
    expected_text: str | None = None
    explanation: str | None = None
    source: object = object()


class FakeAnalyzer:
    def __init__(self, analysis):
        self.analysis = analysis
        self.calls = []

    async def analyze(self, **kwargs):
        self.calls.append(kwargs)
        return self.analysis


class FakePolicy:
    def __init__(self, observations):
        self.observations = observations
        self.calls = []

    async def validate(self, observations):
        self.calls.append(observations)
        return self.observations


class FakeEvidenceService:
    def __init__(self):
        self.calls = []

    async def record(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            evidence=SimpleNamespace(observation_id=kwargs["observation_id"]),
            state=None,
            reinforcement_decision=None,
        )


def _service(*, analysis, accepted):
    analyzer = FakeAnalyzer(analysis)
    policy = FakePolicy(accepted)
    evidence = FakeEvidenceService()
    service = CharacterLearningTurnService(
        analyzer=analyzer,
        observation_policy=policy,
        evidence_service=evidence,
    )
    return service, analyzer, policy, evidence


@pytest.mark.asyncio
async def test_missing_skill_skips_learning_pipeline():
    analysis = SimpleNamespace(observations=[])
    service, analyzer, policy, evidence = _service(
        analysis=analysis,
        accepted=[],
    )

    result = await service.process(
        learner_id="learner-1",
        world_id="french_world",
        skill_id=None,
        observation_id_prefix="telegram:abc",
        learner_text="Bonjour",
        character_response="Bonjour !",
    )

    assert result.analyzed is False
    assert result.persisted is False
    assert result.analysis is None
    assert analyzer.calls == []
    assert policy.calls == []
    assert evidence.calls == []


@pytest.mark.asyncio
async def test_authoritative_skill_runs_analysis_policy_and_evidence():
    observation = FakeObservation(
        observation_id="telegram:abc:grammar-1",
        category="GRAMMAR",
        status="CONFIRMED_ERROR",
        severity="MEDIUM",
        confidence=0.95,
        subtype="article",
        learner_text="Je suis aller",
        expected_text="Je suis allé",
        explanation="Past participle agreement.",
        source="CHARACTER_CONVERSATION",
    )
    analysis = SimpleNamespace(observations=(observation,))
    service, analyzer, policy, evidence = _service(
        analysis=analysis,
        accepted=(observation,),
    )

    result = await service.process(
        learner_id="learner-1",
        world_id="french_world",
        skill_id="grammar",
        observation_id_prefix="telegram:abc",
        learner_text="Je suis aller",
        character_response="Tu veux dire « Je suis allé ».",
    )

    assert result.analyzed is True
    assert result.persisted is True
    assert len(result.evidence_results) == 1
    assert analyzer.calls[0]["skill_id"] == "grammar"
    assert policy.calls == [analysis.observations]
    assert evidence.calls[0]["skill_id"] == "grammar"
    assert evidence.calls[0]["observation_id"] == observation.observation_id


@pytest.mark.asyncio
async def test_service_does_not_modify_skill_id_returned_by_application():
    observation = FakeObservation(
        observation_id="turn-1:expression",
        category="EXPRESSION",
        status="UNCERTAIN",
        severity="LOW",
        confidence=0.90,
    )
    analysis = SimpleNamespace(observations=(observation,))
    service, analyzer, _, _ = _service(
        analysis=analysis,
        accepted=(observation,),
    )

    await service.process(
        learner_id="learner-1",
        world_id="french_world",
        skill_id="conversation_expression",
        observation_id_prefix="turn-1",
        learner_text="text",
        character_response="response",
    )

    assert analyzer.calls[0]["skill_id"] == "conversation_expression"


@pytest.mark.asyncio
async def test_empty_accepted_analysis_is_successful_without_persistence():
    analysis = SimpleNamespace(observations=())
    service, _, _, evidence = _service(
        analysis=analysis,
        accepted=(),
    )

    result = await service.process(
        learner_id="learner-1",
        world_id="french_world",
        skill_id="grammar",
        observation_id_prefix="turn-2",
        learner_text="text",
        character_response="response",
    )

    assert result.analyzed is True
    assert result.persisted is False
    assert result.evidence_results == ()
    assert evidence.calls == []


@pytest.mark.asyncio
async def test_invalid_required_identity_is_rejected():
    service, _, _, _ = _service(
        analysis=SimpleNamespace(observations=()),
        accepted=(),
    )

    with pytest.raises(ValueError, match="learner_id"):
        await service.process(
            learner_id="",
            world_id="french_world",
            skill_id="grammar",
            observation_id_prefix="turn",
            learner_text="text",
            character_response="response",
        )


@pytest.mark.asyncio
async def test_learning_service_exception_can_be_isolated_by_caller():
    class FailingAnalyzer:
        async def analyze(self, **kwargs):
            raise RuntimeError("analysis unavailable")

    service = CharacterLearningTurnService(
        analyzer=FailingAnalyzer(),
        observation_policy=FakePolicy(()),
        evidence_service=FakeEvidenceService(),
    )

    with pytest.raises(RuntimeError, match="analysis unavailable"):
        await service.process(
            learner_id="learner-1",
            world_id="french_world",
            skill_id="grammar",
            observation_id_prefix="turn",
            learner_text="text",
            character_response="response",
        )
