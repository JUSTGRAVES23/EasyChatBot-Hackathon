from __future__ import annotations

from app.project_control_center.domain.models import ProjectDefinition
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
)


def create_production_project_registry() -> InMemoryProjectRegistry:
    """Build the Project Control registry used by production composition."""
    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
        )
    )

    return registry


def test_production_project_registry_registers_easychatbot():
    """Protect the production bootstrap registration of the EasyChatBot project."""
    registry = create_production_project_registry()

    project = registry.get("easychatbot")

    assert project is not None
    assert project.project_id == "easychatbot"
    assert project.name == "EasyChatBot"


def test_production_project_registry_does_not_require_duplicate_registration():
    """Verify the canonical project can be resolved from the production registry."""
    registry = create_production_project_registry()

    project = registry.get("easychatbot")

    assert isinstance(project, ProjectDefinition)
    assert project.project_id == "easychatbot"