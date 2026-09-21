from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.study_material.service import (
    StudyMaterialService,
)
from app.domain.study_material.study_material import (
    StudyMaterial,
    StudyMaterialStatus,
    StudyMaterialType,
)


class FakeStudyMaterialRepository:
    def __init__(
        self,
        *,
        materials: list[StudyMaterial] | None = None,
        material: StudyMaterial | None = None,
    ) -> None:
        self.materials = materials or []
        self.material = material

        self.list_calls: list[str] = []
        self.get_calls: list[tuple[object, str]] = []

    def list_published_by_world(
        self,
        world_id: str,
    ) -> list[StudyMaterial]:
        self.list_calls.append(world_id)
        return self.materials

    def get_published(
        self,
        material_id,
        world_id: str,
    ) -> StudyMaterial | None:
        self.get_calls.append(
            (material_id, world_id)
        )
        return self.material


class FakeLearningWorldCatalogueService:
    def __init__(
        self,
        *,
        should_fail: bool = False,
    ) -> None:
        self.should_fail = should_fail
        self.calls: list[str] = []

    def get_by_identifier(
        self,
        identifier: str,
    ):
        self.calls.append(identifier)

        if self.should_fail:
            raise ValueError(
                f"Learning World not found: {identifier}"
            )

        return object()


def make_material(
    *,
    world_id: str = "french_world",
    status: StudyMaterialStatus = StudyMaterialStatus.PUBLISHED,
    material_type: StudyMaterialType = StudyMaterialType.LESSON,
) -> StudyMaterial:
    now = datetime.now(UTC)

    return StudyMaterial(
        material_id=uuid4(),
        world_id=world_id,
        title="French Lesson 1",
        description="Introduction to French",
        material_type=material_type,
        status=status,
        display_order=1,
        created_at=now,
        updated_at=now,
    )


def make_service(
    *,
    repository: FakeStudyMaterialRepository | None = None,
    catalogue: FakeLearningWorldCatalogueService | None = None,
) -> tuple[
    StudyMaterialService,
    FakeStudyMaterialRepository,
    FakeLearningWorldCatalogueService,
]:
    repository = repository or FakeStudyMaterialRepository()
    catalogue = (
        catalogue
        or FakeLearningWorldCatalogueService()
    )

    service = StudyMaterialService(
        repository=repository,
        world_catalogue_service=catalogue,
    )

    return service, repository, catalogue


def test_requires_repository() -> None:
    catalogue = FakeLearningWorldCatalogueService()

    with pytest.raises(
        ValueError,
        match="repository is required",
    ):
        StudyMaterialService(
            repository=None,  # type: ignore[arg-type]
            world_catalogue_service=catalogue,
        )


def test_requires_world_catalogue_service() -> None:
    repository = FakeStudyMaterialRepository()

    with pytest.raises(
        ValueError,
        match="world_catalogue_service is required",
    ):
        StudyMaterialService(
            repository=repository,
            world_catalogue_service=None,  # type: ignore[arg-type]
        )


def test_list_published_validates_world_through_catalogue() -> None:
    material = make_material()

    service, repository, catalogue = make_service(
        repository=FakeStudyMaterialRepository(
            materials=[material]
        ),
    )

    result = service.list_published(
        world_id=" french_world ",
    )

    assert result == [material]
    assert catalogue.calls == ["french_world"]
    assert repository.list_calls == ["french_world"]


def test_list_published_returns_materials() -> None:
    materials = [
        make_material(
            material_type=StudyMaterialType.READING
        ),
        make_material(
            material_type=StudyMaterialType.EXERCISE
        ),
    ]

    service, repository, _ = make_service(
        repository=FakeStudyMaterialRepository(
            materials=materials
        ),
    )

    result = service.list_published(
        world_id="french_world"
    )

    assert result == materials
    assert repository.list_calls == [
        "french_world"
    ]


def test_list_published_rejects_empty_world_id() -> None:
    service, repository, catalogue = make_service()

    with pytest.raises(
        ValueError,
        match="world_id cannot be empty",
    ):
        service.list_published(world_id="   ")

    assert repository.list_calls == []
    assert catalogue.calls == []


def test_list_published_rejects_non_string_world_id() -> None:
    service, repository, catalogue = make_service()

    with pytest.raises(
        TypeError,
        match="world_id must be a string",
    ):
        service.list_published(
            world_id=None,  # type: ignore[arg-type]
        )

    assert repository.list_calls == []
    assert catalogue.calls == []


def test_list_published_rejects_world_id_over_128_characters() -> None:
    service, repository, catalogue = make_service()

    world_id = "w" * 129

    with pytest.raises(
        ValueError,
        match="world_id is too long",
    ):
        service.list_published(
            world_id=world_id
        )

    assert repository.list_calls == []
    assert catalogue.calls == []


def test_list_published_propagates_world_validation_failure() -> None:
    repository = FakeStudyMaterialRepository()
    catalogue = FakeLearningWorldCatalogueService(
        should_fail=True
    )

    service, _, _ = make_service(
        repository=repository,
        catalogue=catalogue,
    )

    with pytest.raises(
        ValueError,
        match="Learning World not found",
    ):
        service.list_published(
            world_id="french_world"
        )

    assert catalogue.calls == [
        "french_world"
    ]
    assert repository.list_calls == []


def test_list_published_rejects_world_mismatch() -> None:
    material = make_material(
        world_id="spanish_world"
    )

    service, repository, _ = make_service(
        repository=FakeStudyMaterialRepository(
            materials=[material]
        )
    )

    with pytest.raises(
        ValueError,
        match="Study Material World mismatch",
    ):
        service.list_published(
            world_id="french_world"
        )

    assert repository.list_calls == [
        "french_world"
    ]


def test_list_published_rejects_non_published_material() -> None:
    material = make_material(
        status=StudyMaterialStatus.DRAFT
    )

    service, _, _ = make_service(
        repository=FakeStudyMaterialRepository(
            materials=[material]
        )
    )

    with pytest.raises(
        ValueError,
        match="Study Material visibility violation",
    ):
        service.list_published(
            world_id="french_world"
        )


def test_get_published_validates_world_before_repository_lookup() -> None:
    material = make_material()

    service, repository, catalogue = make_service(
        repository=FakeStudyMaterialRepository(
            material=material
        )
    )

    result = service.get_published(
        material_id=material.material_id,
        world_id=" french_world ",
    )

    assert result == material
    assert catalogue.calls == ["french_world"]
    assert repository.get_calls == [
        (
            material.material_id,
            "french_world",
        )
    ]


def test_get_published_returns_none_when_material_not_found() -> None:
    material_id = uuid4()

    service, repository, _ = make_service(
        repository=FakeStudyMaterialRepository(
            material=None
        )
    )

    result = service.get_published(
        material_id=material_id,
        world_id="french_world",
    )

    assert result is None
    assert repository.get_calls == [
        (
            material_id,
            "french_world",
        )
    ]


def test_get_published_rejects_invalid_material_id() -> None:
    service, repository, catalogue = make_service()

    with pytest.raises(
        ValueError,
        match="material_id must be a UUID",
    ):
        service.get_published(
            material_id="not-a-uuid",  # type: ignore[arg-type]
            world_id="french_world",
        )

    assert repository.get_calls == []
    assert catalogue.calls == []


def test_get_published_rejects_empty_world_id() -> None:
    service, repository, catalogue = make_service()

    with pytest.raises(
        ValueError,
        match="world_id cannot be empty",
    ):
        service.get_published(
            material_id=uuid4(),
            world_id="   ",
        )

    assert repository.get_calls == []
    assert catalogue.calls == []


def test_get_published_rejects_world_mismatch() -> None:
    material = make_material(
        world_id="spanish_world"
    )

    service, _, _ = make_service(
        repository=FakeStudyMaterialRepository(
            material=material
        )
    )

    with pytest.raises(
        ValueError,
        match="Study Material World mismatch",
    ):
        service.get_published(
            material_id=material.material_id,
            world_id="french_world",
        )


def test_get_published_rejects_non_published_material() -> None:
    material = make_material(
        status=StudyMaterialStatus.ARCHIVED
    )

    service, _, _ = make_service(
        repository=FakeStudyMaterialRepository(
            material=material
        )
    )

    with pytest.raises(
        ValueError,
        match="Study Material visibility violation",
    ):
        service.get_published(
            material_id=material.material_id,
            world_id="french_world",
        )


def test_get_published_propagates_world_validation_failure() -> None:
    repository = FakeStudyMaterialRepository(
        material=make_material()
    )

    catalogue = FakeLearningWorldCatalogueService(
        should_fail=True
    )

    service, _, _ = make_service(
        repository=repository,
        catalogue=catalogue,
    )

    with pytest.raises(
        ValueError,
        match="Learning World not found",
    ):
        service.get_published(
            material_id=repository.material.material_id,
            world_id="french_world",
        )

    assert repository.get_calls == []


def test_supported_material_types_are_returned() -> None:
    materials = [
        make_material(
            material_type=StudyMaterialType.READING
        ),
        make_material(
            material_type=StudyMaterialType.LESSON
        ),
        make_material(
            material_type=StudyMaterialType.EXERCISE
        ),
    ]

    service, _, _ = make_service(
        repository=FakeStudyMaterialRepository(
            materials=materials
        )
    )

    result = service.list_published(
        world_id="french_world"
    )

    assert [
        material.material_type
        for material in result
    ] == [
        StudyMaterialType.READING,
        StudyMaterialType.LESSON,
        StudyMaterialType.EXERCISE,
    ]