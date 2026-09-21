from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from ..domain.discovery_models import (
    DiscoveryCandidateStatus,
    ProjectDiscoveryCandidate,
)
from ..domain.discovery_ports import ProjectDiscoveryRepository
from .project_registry_service import (
    ProjectAlreadyExistsError,
    ProjectRegistryService,
)


class DiscoveryCandidateNotFoundError(ValueError):
    pass


class DiscoveryCandidateConflictError(ValueError):
    pass


class DiscoveryCandidateStateError(ValueError):
    pass


class ProjectDiscoveryService:
    """Application service for controlled project discovery.

    Discovery candidates are non-authoritative. Acceptance delegates project
    creation to the authoritative ProjectRegistryService and only then marks
    the candidate REGISTERED.

    The persistence adapters currently use independent sessions. Therefore
    acceptance is deliberately made retry-safe: if project creation commits
    before candidate persistence succeeds, a subsequent acceptance can
    reconcile an existing project when its authoritative fields match the
    candidate. A conflicting existing project remains a hard conflict.
    """

    def __init__(
        self,
        *,
        discovery_repository: ProjectDiscoveryRepository,
        project_registry: ProjectRegistryService,
    ) -> None:
        if discovery_repository is None:
            raise ValueError("discovery_repository is required.")
        if project_registry is None:
            raise ValueError("project_registry is required.")

        self._repository = discovery_repository
        self._project_registry = project_registry

    def list_candidates(self) -> list[ProjectDiscoveryCandidate]:
        return self._repository.list_candidates()

    def get_candidate(self, candidate_id: str) -> ProjectDiscoveryCandidate:
        candidate = self._repository.get(candidate_id)
        if candidate is None:
            raise DiscoveryCandidateNotFoundError(
                f"Unknown discovery candidate: {candidate_id}"
            )
        return candidate

    def create_candidate(
        self,
        *,
        candidate_key: str,
        name: str,
        description: str = "",
        owner: str | None = None,
        source: str,
        source_reference: str | None = None,
    ) -> ProjectDiscoveryCandidate:
        candidate_key = self._required(candidate_key, "candidate_key")
        name = self._required(name, "name")
        source = self._required(source, "source")

        if self._repository.find_by_key(candidate_key) is not None:
            raise DiscoveryCandidateConflictError(
                f"Discovery candidate already exists: {candidate_key}"
            )

        return self._repository.save(
            ProjectDiscoveryCandidate(
                candidate_id=str(uuid4()),
                candidate_key=candidate_key,
                name=name,
                description=description.strip(),
                owner=owner.strip() if owner else None,
                source=source,
                source_reference=(
                    source_reference.strip()
                    if source_reference
                    else None
                ),
            )
        )

    def review_candidate(
        self,
        candidate_id: str,
    ) -> ProjectDiscoveryCandidate:
        candidate = self.get_candidate(candidate_id)

        if candidate.status is not DiscoveryCandidateStatus.DISCOVERED:
            raise DiscoveryCandidateStateError(
                "Only DISCOVERED candidates can be reviewed."
            )

        return self._repository.save(
            replace(
                candidate,
                status=DiscoveryCandidateStatus.REVIEWED,
                reviewed_at=datetime.now(timezone.utc),
            )
        )

    def reject_candidate(
        self,
        candidate_id: str,
    ) -> ProjectDiscoveryCandidate:
        candidate = self.get_candidate(candidate_id)

        if candidate.status not in {
            DiscoveryCandidateStatus.DISCOVERED,
            DiscoveryCandidateStatus.REVIEWED,
        }:
            raise DiscoveryCandidateStateError(
                "Only DISCOVERED or REVIEWED candidates can be rejected."
            )

        return self._repository.save(
            replace(
                candidate,
                status=DiscoveryCandidateStatus.REJECTED,
                reviewed_at=datetime.now(timezone.utc),
            )
        )

    def accept_candidate(
        self,
        candidate_id: str,
    ) -> ProjectDiscoveryCandidate:
        candidate = self.get_candidate(candidate_id)

        if candidate.status is not DiscoveryCandidateStatus.REVIEWED:
            raise DiscoveryCandidateStateError(
                "A candidate must be REVIEWED before acceptance."
            )

        try:
            project = self._project_registry.create_project(
                project_id=candidate.candidate_key,
                name=candidate.name,
                description=candidate.description,
                owner=candidate.owner,
                active=True,
            )
        except ProjectAlreadyExistsError as exc:
            # Retry-safe reconciliation:
            # a previous attempt may have committed the authoritative
            # project before the candidate update failed.
            existing_project = self._project_registry.get_project(
                candidate.candidate_key
            )

            if not self._project_matches_candidate(
                existing_project,
                candidate,
            ):
                raise DiscoveryCandidateConflictError(
                    "Project already exists with different authoritative "
                    f"data for candidate: {candidate.candidate_key}"
                ) from exc

            project = existing_project

        return self._repository.save(
            replace(
                candidate,
                status=DiscoveryCandidateStatus.REGISTERED,
                reviewed_at=(
                    candidate.reviewed_at
                    or datetime.now(timezone.utc)
                ),
                registered_project_id=project.project_id,
            )
        )

    @staticmethod
    def _project_matches_candidate(project, candidate) -> bool:
        if project is None:
            return False

        return (
            project.project_id == candidate.candidate_key
            and project.name == candidate.name
            and project.description == candidate.description
            and project.owner == candidate.owner
            and project.active is True
        )

    @staticmethod
    def _required(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required.")
        return value.strip()


__all__ = [
    "DiscoveryCandidateConflictError",
    "DiscoveryCandidateNotFoundError",
    "DiscoveryCandidateStateError",
    "ProjectDiscoveryService",
]
