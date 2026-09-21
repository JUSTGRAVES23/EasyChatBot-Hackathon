from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.postgresql_project_registry import (
    PostgreSQLProjectRegistry,
)
from app.infrastructure.persistence.project_registry_records import (
    ProjectRegistryRecord,
)
from app.project_control_center.domain.models import ProjectDefinition


def _registry():
    engine = create_engine("sqlite:///:memory:")

    ProjectRegistryRecord.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return PostgreSQLProjectRegistry(session_factory), engine


def _project(
    *,
    project_id: str = "easychatbot",
    name: str = "EasyChatBot",
    active: bool = True,
) -> ProjectDefinition:
    return ProjectDefinition(
        project_id=project_id,
        name=name,
        description="AI-powered language learning platform.",
        owner="EasyChatBot Team",
        active=active,
        created_at=datetime.now(timezone.utc),
    )


def _assert_project_equal(
    actual: ProjectDefinition | None,
    expected: ProjectDefinition,
) -> None:
    assert actual is not None
    assert actual.project_id == expected.project_id
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert actual.owner == expected.owner
    assert actual.active == expected.active

    # SQLite does not preserve timezone information for DateTime(timezone=True).
    # Compare the persisted instant rather than SQLite's timezone representation.
    assert actual.created_at.replace(tzinfo=timezone.utc) == (
        expected.created_at
    )


def test_get_returns_none_for_unknown_project() -> None:
    registry, engine = _registry()

    try:
        assert registry.get("unknown") is None
    finally:
        engine.dispose()


def test_save_and_get_round_trip() -> None:
    registry, engine = _registry()
    project = _project()

    try:
        saved = registry.save(project)
        loaded = registry.get("easychatbot")

        assert saved == project
        _assert_project_equal(loaded, project)
    finally:
        engine.dispose()


def test_list_active_returns_only_active_projects() -> None:
    registry, engine = _registry()

    try:
        registry.save(
            _project(
                project_id="active-project",
                name="Active",
            )
        )
        registry.save(
            _project(
                project_id="inactive-project",
                name="Inactive",
                active=False,
            )
        )

        projects = registry.list_active()

        assert [project.project_id for project in projects] == [
            "active-project"
        ]
    finally:
        engine.dispose()


def test_save_updates_existing_project_without_changing_created_at() -> None:
    registry, engine = _registry()

    original = _project()
    registry.save(original)

    updated = ProjectDefinition(
        project_id=original.project_id,
        name="EasyChatBot Updated",
        description="Updated description.",
        owner="Updated Owner",
        active=False,
        created_at=original.created_at,
    )

    try:
        saved = registry.save(updated)
        loaded = registry.get(original.project_id)

        assert saved == updated

        _assert_project_equal(loaded, updated)

        assert loaded is not None
        assert loaded.created_at.replace(tzinfo=timezone.utc) == (
            original.created_at
        )
    finally:
        engine.dispose()


def test_save_requires_project() -> None:
    registry, engine = _registry()

    try:
        try:
            registry.save(None)  # type: ignore[arg-type]
        except ValueError as exc:
            assert str(exc) == "project is required."
        else:
            raise AssertionError("Expected ValueError")
    finally:
        engine.dispose()


def test_repository_requires_session_factory() -> None:
    try:
        PostgreSQLProjectRegistry(None)
    except ValueError as exc:
        assert str(exc) == "session_factory is required."
    else:
        raise AssertionError("Expected ValueError")