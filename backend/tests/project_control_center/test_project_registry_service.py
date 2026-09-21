from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.project_control_center.application.project_registry_service import (
    ProjectAlreadyExistsError,
    ProjectRegistryService,
)
from app.project_control_center.domain.models import ProjectDefinition
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
)


def _project(project_id: str, *, active: bool = True) -> ProjectDefinition:
    return ProjectDefinition(
        project_id=project_id,
        name=f"Project {project_id}",
        description="Test project",
        owner="owner@example.com",
        active=active,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_list_projects_returns_only_active_registry_projects() -> None:
    registry = InMemoryProjectRegistry()
    registry.save(_project("active"))
    registry.save(_project("inactive", active=False))

    service = ProjectRegistryService(registry)

    projects = service.list_projects()

    assert [project.project_id for project in projects] == ["active"]


def test_create_project_persists_authoritative_definition() -> None:
    registry = InMemoryProjectRegistry()
    service = ProjectRegistryService(registry)

    project = service.create_project(
        project_id="easychatbot",
        name="EasyChatBot",
        description="AI learning platform",
        owner="team",
    )

    assert registry.get("easychatbot") == project
    assert project.name == "EasyChatBot"
    assert project.description == "AI learning platform"
    assert project.owner == "team"
    assert project.active is True


def test_duplicate_project_id_is_rejected() -> None:
    registry = InMemoryProjectRegistry()
    registry.save(_project("easychatbot"))
    service = ProjectRegistryService(registry)

    with pytest.raises(ProjectAlreadyExistsError):
        service.create_project(
            project_id="easychatbot",
            name="Duplicate",
        )


def test_get_unknown_project_returns_none() -> None:
    service = ProjectRegistryService(InMemoryProjectRegistry())

    assert service.get_project("missing") is None


def test_update_preserves_project_id_and_created_at() -> None:
    registry = InMemoryProjectRegistry()
    original = _project("easychatbot")
    registry.save(original)
    service = ProjectRegistryService(registry)

    updated = service.update_project(
        "easychatbot",
        name="EasyChatBot Updated",
        description="Updated description",
        owner="new-owner",
        active=False,
    )

    assert updated is not None
    assert updated.project_id == original.project_id
    assert updated.created_at == original.created_at
    assert updated.name == "EasyChatBot Updated"
    assert updated.description == "Updated description"
    assert updated.owner == "new-owner"
    assert updated.active is False


def test_update_unknown_project_returns_none() -> None:
    service = ProjectRegistryService(InMemoryProjectRegistry())

    assert service.update_project("missing", name="Nope") is None


def test_invalid_project_id_and_name_are_rejected() -> None:
    service = ProjectRegistryService(InMemoryProjectRegistry())

    with pytest.raises(ValueError, match="project_id is required"):
        service.create_project(project_id=" ", name="Valid")

    with pytest.raises(ValueError, match="name is required"):
        service.create_project(project_id="valid", name=" ")


def test_update_does_not_replace_unspecified_fields() -> None:
    registry = InMemoryProjectRegistry()
    original = _project("easychatbot")
    registry.save(original)
    service = ProjectRegistryService(registry)

    updated = service.update_project(
        "easychatbot",
        name="Renamed",
    )

    assert updated is not None
    assert updated.name == "Renamed"
    assert updated.description == original.description
    assert updated.owner == original.owner
    assert updated.active == original.active
    assert updated.created_at == original.created_at
