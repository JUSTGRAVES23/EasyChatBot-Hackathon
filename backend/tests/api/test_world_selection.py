from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import world_selection
from app.api.world_selection import router


@dataclass(frozen=True)
class Principal:
    user_id: str
    is_active: bool = True


@dataclass(frozen=True)
class Result:
    world_id: str


class FakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def assign_world(
        self,
        *,
        user_id: str,
        world_identifier: str,
    ) -> Result:
        self.calls.append((user_id, world_identifier))

        return Result(
            world_id="french_world",
        )


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()

    app.state.world_selection_service = FakeService()

    async def fake_principal() -> Principal:
        return Principal(
            user_id="authenticated-user",
        )

    # FastAPI captures the dependency declared by Depends(...).
    # Use the supported dependency override mechanism so the test
    # exercises the real API dependency boundary without requiring
    # the production authentication repository.
    app.dependency_overrides[
        world_selection.get_current_principal
    ] = fake_principal

    app.include_router(
        router,
        prefix="/api",
    )

    return TestClient(app)


def test_select_world_uses_authenticated_principal(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/world-selection",
        json={
            "world_id": "french",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "world_id": "french_world",
    }

    service = client.app.state.world_selection_service

    assert service.calls == [
        (
            "authenticated-user",
            "french",
        ),
    ]


def test_select_world_does_not_accept_caller_user_id(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/world-selection",
        json={
            "world_id": "french",
            "user_id": "attacker",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "world_id": "french_world",
    }

    service = client.app.state.world_selection_service

    # The API must derive the identity from the authenticated
    # principal. A caller-supplied user_id must never become
    # authoritative.
    assert service.calls == [
        (
            "authenticated-user",
            "french",
        ),
    ]