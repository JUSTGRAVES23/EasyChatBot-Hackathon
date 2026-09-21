from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.study_material import router
from app.domain.identity.principal import AccountStatus, Principal
from app.domain.study_material.study_material import (
    StudyMaterial,
    StudyMaterialStatus,
    StudyMaterialType,
)


def make_principal(
    *,
    user_id: str = "learner-001",
) -> Principal:
    return Principal(
        user_id=user_id,
        email=f"{user_id}@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(),
    )


def make_material(
    *,
    material_id: UUID | None = None,
    world_id: str = "french_world",
    title: str = "French Lesson 1",
    description: str | None = "Introduction to French",
    material_type: StudyMaterialType = StudyMaterialType.LESSON,
    status: StudyMaterialStatus = StudyMaterialStatus.PUBLISHED,
    display_order: int = 1,
) -> StudyMaterial:
    now = datetime.now(timezone.utc)

    return StudyMaterial(
        material_id=material_id or uuid4(),
        world_id=world_id,
        title=title,
        description=description,
        material_type=material_type,
        status=status,
        display_order=display_order,
        created_at=now,
        updated_at=now,
    )


class FakeStudyMaterialService:
    def __init__(self) -> None:
        self.material = make_material()

        self.list_calls: list[str] = []

        self.get_calls: list[
            tuple[UUID, str]
        ] = []

    def list_published(
        self,
        *,
        world_id: str,
    ) -> list[StudyMaterial]:
        self.list_calls.append(world_id)

        return [self.material]

    def get_published(
        self,
        *,
        material_id: UUID,
        world_id: str,
    ) -> StudyMaterial | None:
        self.get_calls.append(
            (
                material_id,
                world_id,
            )
        )

        if (
            material_id
            == self.material.material_id
            and world_id
            == self.material.world_id
        ):
            return self.material

        return None


@pytest.fixture
def study_material_service() -> FakeStudyMaterialService:
    return FakeStudyMaterialService()


@pytest.fixture
def app(
    study_material_service: FakeStudyMaterialService,
) -> FastAPI:
    application = FastAPI()

    application.include_router(router)

    application.state.study_material_service = (
        study_material_service
    )

    return application


@pytest.fixture
def client(
    app: FastAPI,
) -> TestClient:
    async def fake_get_current_principal() -> Principal:
        return make_principal()

    app.dependency_overrides[
        get_current_principal
    ] = fake_get_current_principal

    return TestClient(app)


def test_list_published_materials_returns_catalogue(
    client: TestClient,
    study_material_service: FakeStudyMaterialService,
) -> None:
    response = client.get(
        "/api/learning/worlds/french_world/materials",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["world_id"] == "french_world"

    assert len(payload["materials"]) == 1

    material = payload["materials"][0]

    assert material["material_id"] == str(
        study_material_service.material.material_id
    )

    assert material["title"] == "French Lesson 1"

    assert material["description"] == (
        "Introduction to French"
    )

    assert material["material_type"] == "LESSON"

    assert material["status"] == "PUBLISHED"

    assert material["display_order"] == 1

    assert study_material_service.list_calls == [
        "french_world"
    ]


def test_get_published_material_returns_material(
    client: TestClient,
    study_material_service: FakeStudyMaterialService,
) -> None:
    material_id = (
        study_material_service.material.material_id
    )

    response = client.get(
        f"/api/learning/worlds/"
        f"french_world/materials/{material_id}",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["material_id"] == str(
        material_id
    )

    assert payload["world_id"] == "french_world"

    assert payload["material_type"] == "LESSON"

    assert payload["status"] == "PUBLISHED"

    assert study_material_service.get_calls == [
        (
            material_id,
            "french_world",
        )
    ]


def test_unknown_material_returns_404(
    client: TestClient,
) -> None:
    unknown_material_id = uuid4()

    response = client.get(
        f"/api/learning/worlds/"
        f"french_world/materials/{unknown_material_id}",
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Study Material not found."
    )


def test_invalid_material_uuid_returns_422(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/learning/worlds/"
        "french_world/materials/not-a-uuid",
    )

    assert response.status_code == 422


def test_invalid_world_is_mapped_to_404(
    app: FastAPI,
) -> None:
    class InvalidWorldService(
        FakeStudyMaterialService
    ):
        def list_published(
            self,
            *,
            world_id: str,
        ) -> list[StudyMaterial]:
            raise ValueError(
                "Learning World not found."
            )

    service = InvalidWorldService()

    app.state.study_material_service = service

    async def fake_get_current_principal() -> Principal:
        return make_principal()

    app.dependency_overrides[
        get_current_principal
    ] = fake_get_current_principal

    with TestClient(app) as test_client:
        response = test_client.get(
            "/api/learning/worlds/"
            "unknown_world/materials",
        )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Learning World not found."
    )


def test_authentication_is_required(
    app: FastAPI,
) -> None:
    async def reject_current_principal() -> Principal:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    app.dependency_overrides[
        get_current_principal
    ] = reject_current_principal

    with TestClient(app) as test_client:
        response = test_client.get(
            "/api/learning/worlds/"
            "french_world/materials",
        )

    assert response.status_code == 401


def test_client_cannot_supply_learner_identity(
    client: TestClient,
    study_material_service: FakeStudyMaterialService,
) -> None:
    response = client.get(
        "/api/learning/worlds/"
        "french_world/materials",
        params={
            "learner_id": "attacker-learner",
            "telegram_user_id": "123456789",
            "conversation_id": str(uuid4()),
        },
    )

    assert response.status_code == 200

    assert study_material_service.list_calls == [
        "french_world"
    ]