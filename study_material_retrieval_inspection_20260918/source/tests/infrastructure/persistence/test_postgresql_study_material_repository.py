from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.domain.study_material.study_material import (
    StudyMaterialStatus,
    StudyMaterialType,
)
from app.infrastructure.persistence.postgresql_study_material_repository import (
    PostgreSQLStudyMaterialRepository,
)
from app.infrastructure.persistence.study_material_models import (
    StudyMaterialRecord,
)


class FakeScalars:
    """Minimal SQLAlchemy scalars result double."""

    def __init__(self, records: list[object]) -> None:
        self._records = records

    def all(self) -> list[object]:
        return self._records


class FakeSession:
    """Minimal session double for repository unit tests."""

    def __init__(self) -> None:
        self.scalar_result: object | None = None
        self.scalars_result: list[object] = []
        self.statements: list[object] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None

    def scalar(self, statement: object) -> object | None:
        self.statements.append(statement)
        return self.scalar_result

    def scalars(self, statement: object) -> FakeScalars:
        self.statements.append(statement)
        return FakeScalars(self.scalars_result)


class FakeSessionFactory:
    """Callable session factory matching the production boundary."""

    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.calls = 0

    def __call__(self) -> FakeSession:
        self.calls += 1
        return self.session


def make_record(
    *,
    material_id: UUID | None = None,
    title: str = "French Greetings",
    description: str | None = "Basic greetings in French.",
    material_type: str = "LESSON",
    status: str = "PUBLISHED",
    display_order: int = 0,
) -> StudyMaterialRecord:
    now = datetime.now(timezone.utc)

    return StudyMaterialRecord(
        material_id=material_id or uuid4(),
        world_id=uuid4(),
        title=title,
        description=description,
        material_type=material_type,
        status=status,
        display_order=display_order,
        created_at=now,
        updated_at=now,
    )


def test_repository_rejects_none_session_factory() -> None:
    with pytest.raises(
        ValueError,
        match="session_factory cannot be None",
    ):
        PostgreSQLStudyMaterialRepository(None)  # type: ignore[arg-type]


def test_list_published_by_world_returns_domain_models() -> None:
    first = make_record(
        title="French Greetings",
        material_type="LESSON",
        status="PUBLISHED",
        display_order=0,
    )
    second = make_record(
        title="Everyday Vocabulary",
        material_type="READING",
        status="PUBLISHED",
        display_order=1,
    )

    session = FakeSession()
    session.scalars_result = [first, second]

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.list_published_by_world(
        "french_world",
    )

    assert factory.calls == 1
    assert len(result) == 2

    assert result[0].material_id == first.material_id
    assert result[0].world_id == "french_world"
    assert result[0].title == "French Greetings"
    assert result[0].description == "Basic greetings in French."
    assert result[0].material_type is StudyMaterialType.LESSON
    assert result[0].status is StudyMaterialStatus.PUBLISHED
    assert result[0].display_order == 0

    assert result[1].material_id == second.material_id
    assert result[1].world_id == "french_world"
    assert result[1].title == "Everyday Vocabulary"
    assert result[1].material_type is StudyMaterialType.READING
    assert result[1].status is StudyMaterialStatus.PUBLISHED
    assert result[1].display_order == 1


def test_list_published_by_world_returns_empty_list_when_none_exist() -> None:
    session = FakeSession()
    session.scalars_result = []

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.list_published_by_world(
        "french_world",
    )

    assert result == []
    assert factory.calls == 1


def test_get_published_returns_matching_domain_model() -> None:
    material_id = uuid4()

    record = make_record(
        material_id=material_id,
        title="French Exercise",
        description=None,
        material_type="EXERCISE",
        status="PUBLISHED",
        display_order=3,
    )

    session = FakeSession()
    session.scalar_result = record

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.get_published(
        material_id=material_id,
        world_id="french_world",
    )

    assert factory.calls == 1
    assert result is not None

    assert result.material_id == material_id
    assert result.world_id == "french_world"
    assert result.title == "French Exercise"
    assert result.description is None
    assert result.material_type is StudyMaterialType.EXERCISE
    assert result.status is StudyMaterialStatus.PUBLISHED
    assert result.display_order == 3


def test_get_published_returns_none_when_not_found() -> None:
    material_id = uuid4()

    session = FakeSession()
    session.scalar_result = None

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.get_published(
        material_id=material_id,
        world_id="french_world",
    )

    assert result is None
    assert factory.calls == 1


def test_list_published_by_world_rejects_empty_world_id() -> None:
    session = FakeSession()
    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    with pytest.raises(
        ValueError,
        match="world_id cannot be empty",
    ):
        repository.list_published_by_world("   ")

    assert factory.calls == 0


def test_list_published_by_world_rejects_non_string_world_id() -> None:
    session = FakeSession()
    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    with pytest.raises(
        TypeError,
        match="world_id must be a string",
    ):
        repository.list_published_by_world(123)  # type: ignore[arg-type]

    assert factory.calls == 0


def test_get_published_rejects_invalid_material_id() -> None:
    session = FakeSession()
    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    with pytest.raises(
        ValueError,
        match="material_id must be a UUID",
    ):
        repository.get_published(
            material_id="not-a-uuid",  # type: ignore[arg-type]
            world_id="french_world",
        )

    assert factory.calls == 0


def test_get_published_rejects_empty_world_id() -> None:
    session = FakeSession()
    factory = FakeSessionFactory(session)

    repository = PostgreSQLStudyMaterialRepository(factory)

    with pytest.raises(
        ValueError,
        match="world_id cannot be empty",
    ):
        repository.get_published(
            material_id=uuid4(),
            world_id="   ",
        )

    assert factory.calls == 0


def test_repository_rejects_unsupported_material_type() -> None:
    record = make_record(
        material_type="VIDEO",
        status="PUBLISHED",
    )

    session = FakeSession()
    session.scalar_result = record

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    with pytest.raises(
        ValueError,
        match="Unsupported Study Material type",
    ):
        repository.get_published(
            material_id=record.material_id,
            world_id="french_world",
        )


def test_repository_rejects_unsupported_material_status() -> None:
    record = make_record(
        material_type="LESSON",
        status="INVALID",
    )

    session = FakeSession()
    session.scalar_result = record

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    with pytest.raises(
        ValueError,
        match="Unsupported Study Material status",
    ):
        repository.get_published(
            material_id=record.material_id,
            world_id="french_world",
        )


def test_repository_accepts_all_supported_material_types() -> None:
    records = [
        make_record(
            material_type="READING",
            status="PUBLISHED",
        ),
        make_record(
            material_type="LESSON",
            status="PUBLISHED",
        ),
        make_record(
            material_type="EXERCISE",
            status="PUBLISHED",
        ),
    ]

    session = FakeSession()
    session.scalars_result = records

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.list_published_by_world(
        "french_world",
    )

    assert [item.material_type for item in result] == [
        StudyMaterialType.READING,
        StudyMaterialType.LESSON,
        StudyMaterialType.EXERCISE,
    ]


def test_repository_uses_business_world_identifier_in_domain_result() -> None:
    record = make_record(
        status="PUBLISHED",
    )

    session = FakeSession()
    session.scalar_result = record

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.get_published(
        material_id=record.material_id,
        world_id="luxembourgish_world",
    )

    assert result is not None
    assert result.world_id == "luxembourgish_world"
    assert result.world_id != str(record.world_id)


def test_repository_preserves_material_timestamps() -> None:
    created_at = datetime(
        2026,
        9,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )
    updated_at = datetime(
        2026,
        9,
        17,
        13,
        0,
        tzinfo=timezone.utc,
    )

    record = StudyMaterialRecord(
        material_id=uuid4(),
        world_id=uuid4(),
        title="French Lesson",
        description="Lesson description",
        material_type="LESSON",
        status="PUBLISHED",
        display_order=5,
        created_at=created_at,
        updated_at=updated_at,
    )

    session = FakeSession()
    session.scalar_result = record

    factory = FakeSessionFactory(session)
    repository = PostgreSQLStudyMaterialRepository(factory)

    result = repository.get_published(
        material_id=record.material_id,
        world_id="french_world",
    )

    assert result is not None
    assert result.created_at == created_at
    assert result.updated_at == updated_at