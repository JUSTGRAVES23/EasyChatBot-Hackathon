from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.learner_context.models import (
    LearnerContext,
    LearnerContextMemory,
    LearnerContextMessage,
)
from app.application.learner_context.service import LearnerContextService


@dataclass
class FakeLearnerContextRepository:
    context: LearnerContext | None

    async def get(
        self,
        *,
        learner_id: str,
        world_id: str,
        recent_limit: int,
    ) -> LearnerContext | None:
        if self.context is None:
            return None

        return self.context


def make_context() -> LearnerContext:
    return LearnerContext(
        learner_id="learner-1",
        world_id="polish",
        language_code="pl",
        character="Alix",
        level="B1",
        telegram_connected=True,
        learning_memories=(
            LearnerContextMemory(
                memory_type="vocabulary",
                content="Practising travel vocabulary.",
            ),
        ),
        recent_learning_context=(
            LearnerContextMessage(
                role="user",
                content="I want to practise restaurant vocabulary.",
            ),
            LearnerContextMessage(
                role="assistant",
                content="Let's practise ordering food.",
            ),
        ),
    )


@pytest.mark.asyncio
async def test_returns_canonical_context() -> None:
    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=make_context(),
        ),
    )

    result = await service.get(
        learner_id="learner-1",
        world_id="polish",
    )

    assert result.learner_id == "learner-1"
    assert result.world_id == "polish"
    assert result.telegram_connected is True
    assert result.learning_memories[0].memory_type == "vocabulary"


@pytest.mark.asyncio
async def test_rejects_empty_learner_id() -> None:
    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=make_context(),
        ),
    )

    with pytest.raises(ValueError, match="learner_id cannot be empty"):
        await service.get(
            learner_id=" ",
            world_id="polish",
        )


@pytest.mark.asyncio
async def test_rejects_empty_world_id() -> None:
    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=make_context(),
        ),
    )

    with pytest.raises(ValueError, match="world_id cannot be empty"):
        await service.get(
            learner_id="learner-1",
            world_id=" ",
        )


@pytest.mark.asyncio
async def test_rejects_invalid_recent_limit() -> None:
    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=make_context(),
        ),
    )

    with pytest.raises(ValueError, match="recent_limit"):
        await service.get(
            learner_id="learner-1",
            world_id="polish",
            recent_limit=0,
        )


@pytest.mark.asyncio
async def test_missing_context_is_rejected() -> None:
    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=None,
        ),
    )

    with pytest.raises(ValueError, match="Learner context not found"):
        await service.get(
            learner_id="learner-1",
            world_id="polish",
        )


@pytest.mark.asyncio
async def test_ownership_mismatch_is_rejected() -> None:
    context = make_context()
    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=context,
        ),
    )

    with pytest.raises(ValueError, match="ownership mismatch"):
        await service.get(
            learner_id="another-learner",
            world_id="polish",
        )


@pytest.mark.asyncio
async def test_world_mismatch_is_rejected() -> None:
    context = LearnerContext(
        learner_id="learner-1",
        world_id="french_world",
        language_code="fr",
        character="Alix",
        level="B1",
        telegram_connected=True,
        learning_memories=(),
        recent_learning_context=(),
    )

    service = LearnerContextService(
        repository=FakeLearnerContextRepository(
            context=context,
        ),
    )

    with pytest.raises(ValueError, match="World mismatch"):
        await service.get(
            learner_id="learner-1",
            world_id="polish",
        )
