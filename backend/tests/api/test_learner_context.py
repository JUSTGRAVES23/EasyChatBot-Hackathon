from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.learner_context import router
from app.application.learner_context.models import (
    LearnerContext,
    LearnerContextMemory,
    LearnerContextMessage,
)
from app.domain.identity.principal import (
    AccountStatus,
    Principal,
)


@dataclass
class FakeLearnerContextService:
    context: LearnerContext | None = None
    error: Exception | None = None
    calls: list[tuple[str, str]] | None = None

    async def get(
        self,
        *,
        learner_id: str,
        world_id: str,
        recent_limit: int = 20,
    ):
        if self.calls is None:
            self.calls = []

        self.calls.append(
            (learner_id, world_id),
        )

        if self.error is not None:
            raise self.error

        assert self.context is not None
        return self.context


def build_app(
    service: FakeLearnerContextService,
) -> FastAPI:
    app = FastAPI()
    app.state.learner_context_service = service

    async def fake_principal() -> Principal:
        return Principal(
            user_id="academy-user-1",
            email="learner@example.com",
            email_verified=True,
            account_status=AccountStatus.ACTIVE,
        )

    app.dependency_overrides[
        get_current_principal
    ] = fake_principal

    app.include_router(
        router,
        prefix="/api",
    )

    return app


def test_authenticated_learner_context_is_returned():
    service = FakeLearnerContextService(
        context=LearnerContext(
            learner_id="academy-user-1",
            world_id="polish_world",
            language_code="pl",
            character="Alix",
            level="B1",
            telegram_connected=True,
            learning_memories=(
                LearnerContextMemory(
                    memory_type="vocabulary",
                    content="food",
                ),
            ),
            recent_learning_context=(
                LearnerContextMessage(
                    role="user",
                    content="I practised Polish yesterday.",
                ),
            ),
        ),
    )

    app = build_app(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/learner-context",
            params={
                "world_id": "polish_world",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["learner_id"] == "academy-user-1"
    assert payload["world_id"] == "polish_world"
    assert payload["language_code"] == "pl"
    assert payload["character"] == "Alix"
    assert payload["level"] == "B1"
    assert payload["telegram_connected"] is True

    assert payload["learning_memories"] == [
        {
            "memory_type": "vocabulary",
            "content": "food",
        },
    ]

    assert payload["recent_learning_context"] == [
        {
            "role": "user",
            "content": "I practised Polish yesterday.",
        },
    ]

    assert service.calls == [
        ("academy-user-1", "polish_world"),
    ]


def test_client_cannot_supply_learner_identity():
    service = FakeLearnerContextService(
        context=LearnerContext(
            learner_id="academy-user-1",
            world_id="polish_world",
            language_code="pl",
            character="Alix",
            level="B1",
            telegram_connected=False,
            learning_memories=(),
            recent_learning_context=(),
        ),
    )

    app = build_app(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/learner-context",
            params={
                "world_id": "polish_world",
                "learner_id": "attacker",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["learner_id"] == "academy-user-1"

    assert service.calls == [
        ("academy-user-1", "polish_world"),
    ]


def test_world_not_found_maps_to_404():
    service = FakeLearnerContextService(
        error=ValueError(
            "World not found: unknown_world",
        ),
    )

    app = build_app(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/learner-context",
            params={
                "world_id": "unknown_world",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "World not found: unknown_world"
    )