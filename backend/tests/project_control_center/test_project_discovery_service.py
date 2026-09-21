from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.project_control_center.application.project_discovery_service import (
    DiscoveryCandidateConflictError,
    DiscoveryCandidateStateError,
    ProjectDiscoveryService,
)
from app.project_control_center.domain.discovery_models import (
    DiscoveryCandidateStatus,
    ProjectDiscoveryCandidate,
)
from app.project_control_center.domain.models import ProjectDefinition


class FakeDiscoveryRepository:
    def __init__(self) -> None:
        self.items: dict[str, ProjectDiscoveryCandidate] = {}

    def get(self, candidate_id: str):
        return self.items.get(candidate_id)

    def list_candidates(self):
        return list(self.items.values())

    def find_by_key(self, candidate_key: str):
        return next(
            (
                candidate
                for candidate in self.items.values()
                if candidate.candidate_key == candidate_key
            ),
            None,
        )

    def save(self, candidate):
        self.items[candidate.candidate_id] = candidate
        return candidate


class FakeProjectRegistry:
    def __init__(self) -> None:
        self.projects: dict[str, ProjectDefinition] = {}

    def get_project(self, project_id: str):
        project = self.projects.get(project_id)
        if project is None:
            from app.project_control_center.application.project_registry_service import (
                ProjectNotFoundError,
            )

            raise ProjectNotFoundError(project_id)

        return project

    def create_project(self, **kwargs):
        from app.project_control_center.application.project_registry_service import (
            ProjectAlreadyExistsError,
        )

        if kwargs["project_id"] in self.projects:
            raise ProjectAlreadyExistsError(kwargs["project_id"])

        project = ProjectDefinition(
            project_id=kwargs["project_id"],
            name=kwargs["name"],
            description=kwargs["description"],
            owner=kwargs["owner"],
            active=kwargs["active"],
            created_at=datetime.now(timezone.utc),
        )
        self.projects[project.project_id] = project
        return project


def _service() -> tuple[
    ProjectDiscoveryService,
    FakeDiscoveryRepository,
    FakeProjectRegistry,
]:
    discovery = FakeDiscoveryRepository()
    registry = FakeProjectRegistry()
    service = ProjectDiscoveryService(
        discovery_repository=discovery,
        project_registry=registry,
    )
    return service, discovery, registry


def _reviewed_candidate(
    discovery: FakeDiscoveryRepository,
) -> ProjectDiscoveryCandidate:
    candidate = ProjectDiscoveryCandidate(
        candidate_id="candidate-1",
        candidate_key="project-x",
        name="Project X",
        description="A project",
        owner="owner@example.com",
        source="internal",
        discovered_at=datetime.now(timezone.utc),
    )
    discovery.save(candidate)

    reviewed = replace(
        candidate,
        status=DiscoveryCandidateStatus.REVIEWED,
        reviewed_at=datetime.now(timezone.utc),
    )
    discovery.save(reviewed)
    return reviewed


def test_accept_registers_project_and_candidate():
    service, discovery, registry = _service()
    candidate = _reviewed_candidate(discovery)

    result = service.accept_candidate(candidate.candidate_id)

    assert result.status is DiscoveryCandidateStatus.REGISTERED
    assert result.registered_project_id == "project-x"
    assert "project-x" in registry.projects


def test_accept_reconciles_existing_matching_project():
    service, discovery, registry = _service()
    candidate = _reviewed_candidate(discovery)

    registry.projects["project-x"] = ProjectDefinition(
        project_id="project-x",
        name="Project X",
        description="A project",
        owner="owner@example.com",
        active=True,
        created_at=datetime.now(timezone.utc),
    )

    result = service.accept_candidate(candidate.candidate_id)

    assert result.status is DiscoveryCandidateStatus.REGISTERED
    assert result.registered_project_id == "project-x"


def test_accept_rejects_conflicting_existing_project():
    service, discovery, registry = _service()
    candidate = _reviewed_candidate(discovery)

    registry.projects["project-x"] = ProjectDefinition(
        project_id="project-x",
        name="Different Project",
        description="Different data",
        owner="other@example.com",
        active=True,
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(DiscoveryCandidateConflictError):
        service.accept_candidate(candidate.candidate_id)


def test_accept_requires_review():
    service, discovery, _ = _service()

    candidate = service.create_candidate(
        candidate_key="project-y",
        name="Project Y",
        source="internal",
    )

    with pytest.raises(DiscoveryCandidateStateError):
        service.accept_candidate(candidate.candidate_id)
