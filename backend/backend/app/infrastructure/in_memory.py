from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.models import ProjectControlSnapshot, ProjectDefinition, ProjectEvent
from ..domain.ports import (
    ProjectEventRepository,
    ProjectRegistry,
    SnapshotRepository,
)


@dataclass
class InMemoryProjectRegistry(ProjectRegistry):
    projects: dict[str, ProjectDefinition] = field(default_factory=dict)

    def get(self, project_id: str) -> ProjectDefinition | None:
        return self.projects.get(project_id)

    def list_active(self) -> list[ProjectDefinition]:
        return [p for p in self.projects.values() if p.active]

    def save(self, project: ProjectDefinition) -> ProjectDefinition:
        self.projects[project.project_id] = project
        return project


@dataclass
class InMemorySnapshotRepository(SnapshotRepository):
    data: dict[str, list[ProjectControlSnapshot]] = field(default_factory=dict)

    def save(self, snapshot: ProjectControlSnapshot) -> ProjectControlSnapshot:
        self.data.setdefault(snapshot.project_id, []).insert(0, snapshot)
        return snapshot

    def list_for_project(
        self, project_id: str, limit: int = 30
    ) -> list[ProjectControlSnapshot]:
        return self.data.get(project_id, [])[:limit]


@dataclass
class InMemoryProjectEventRepository(ProjectEventRepository):
    data: dict[str, list[ProjectEvent]] = field(default_factory=dict)

    def save(self, event: ProjectEvent) -> ProjectEvent:
        self.data.setdefault(event.project_id, []).insert(0, event)
        return event

    def list_for_project(
        self, project_id: str, limit: int = 100
    ) -> list[ProjectEvent]:
        return self.data.get(project_id, [])[:limit]
