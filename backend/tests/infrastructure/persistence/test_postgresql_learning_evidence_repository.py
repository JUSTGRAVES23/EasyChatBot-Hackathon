import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.domain.learning_assessment.learning_evidence import (
    LearningEvidence,
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)
from app.infrastructure.persistence.postgresql_learning_evidence_repository import (
    PostgreSQLLearningEvidenceRepository,
)


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.existing = None
        self.world = SimpleNamespace(
            id=uuid4(),
            identifier="french",
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def scalar(self, statement):
        return self.world

    def execute(self, statement):
        class Result:
            def __init__(self, value):
                self.value = value

            def first(self):
                return self.value

            def all(self):
                return []

        return Result(self.existing)

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.committed = True

    def refresh(self, row):
        return None


class FakeSessionFactory:
    def __init__(self):
        self.session = FakeSession()

    def __call__(self):
        return self.session


def test_repository_save_resolves_existing_world_and_maps_evidence():
    factory = FakeSessionFactory()
    repository = PostgreSQLLearningEvidenceRepository(factory)

    evidence = LearningEvidence(
        evidence_id="e1",
        observation_id="obs-1",
        learner_id="learner-1",
        world_id="french",
        skill_id="grammar.past_tense",
        category=LearningEvidenceCategory.GRAMMAR,
        status=LearningEvidenceStatus.CONFIRMED_ERROR,
        severity=LearningEvidenceSeverity.HIGH,
        confidence=0.98,
        subtype="past_tense",
        learner_text="Je vais hier.",
        expected_text="Je suis allé hier.",
        explanation="Past tense mismatch.",
        source=LearningEvidenceSource.CHARACTER_CONVERSATION,
        created_at=datetime.now(timezone.utc),
    )

    saved = asyncio.run(repository.save(evidence))

    assert saved == evidence
    assert len(factory.session.added) == 1
    assert factory.session.added[0].world_id == factory.session.world.id
    assert factory.session.committed is True
