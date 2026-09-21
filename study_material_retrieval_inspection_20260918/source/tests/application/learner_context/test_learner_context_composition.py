from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.composition.learner_context_composition import (
    build_learner_context_service,
)
from app.application.learner_context.models import (
    LearnerContext,
)
from app.application.learner_context.service import (
    LearnerContextService,
)


class FakeBindingRepository:
    pass


class FakeMemoryRepository:
    pass


class FakeEventRepository:
    pass


class FakePrivacyService:
    pass


class FakeWorldResolver:
    pass


def test_builds_service_from_existing_ports():
    service = build_learner_context_service(
        telegram_bindings=FakeBindingRepository(),
        memory_repository=FakeMemoryRepository(),
        conversation_event_repository=FakeEventRepository(),
        privacy_identifier_service=FakePrivacyService(),
        world_resolver=FakeWorldResolver(),
    )

    assert isinstance(service, LearnerContextService)


def test_composition_requires_existing_session_factory():
    from app.application.composition.learner_context_composition import (
        build_production_learner_context_service,
    )

    with pytest.raises(ValueError, match="session_factory is required"):
        build_production_learner_context_service(
            session_factory=None,
        )
