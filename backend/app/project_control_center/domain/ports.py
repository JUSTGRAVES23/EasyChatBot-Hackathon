from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    ActionSnapshot,
    IssueSnapshot,
    MetricSnapshot,
    MilestoneSnapshot,
    ProjectDefinition,
    ProjectEvent,
    ProjectControlSnapshot,
    RiskSnapshot,
    SourceSnapshot,
    WorkstreamSnapshot,
)


class ProjectRegistry(ABC):
    @abstractmethod
    def get(self, project_id: str) -> ProjectDefinition | None: ...

    @abstractmethod
    def list_active(self) -> list[ProjectDefinition]: ...

    @abstractmethod
    def save(self, project: ProjectDefinition) -> ProjectDefinition: ...


class ProjectStatusSource(ABC):
    """Read-only adapter over an existing authoritative EasyChatBot source."""

    @property
    @abstractmethod
    def source_id(self) -> str: ...

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def fetch_workstreams(self, project_id: str) -> list[WorkstreamSnapshot]: ...

    @abstractmethod
    def fetch_metrics(self, project_id: str) -> list[MetricSnapshot]: ...

    @abstractmethod
    def fetch_issues(self, project_id: str) -> list[IssueSnapshot]: ...

    @abstractmethod
    def fetch_risks(self, project_id: str) -> list[RiskSnapshot]: ...

    @abstractmethod
    def fetch_actions(self, project_id: str) -> list[ActionSnapshot]: ...

    @abstractmethod
    def fetch_milestones(self, project_id: str) -> list[MilestoneSnapshot]: ...

    @abstractmethod
    def health(self) -> SourceSnapshot: ...


class SnapshotRepository(ABC):
    @abstractmethod
    def save(self, snapshot: ProjectControlSnapshot) -> ProjectControlSnapshot: ...

    @abstractmethod
    def list_for_project(self, project_id: str, limit: int = 30) -> list[ProjectControlSnapshot]: ...


class ProjectEventRepository(ABC):
    @abstractmethod
    def save(self, event: ProjectEvent) -> ProjectEvent: ...

    @abstractmethod
    def list_for_project(self, project_id: str, limit: int = 100) -> list[ProjectEvent]: ...
