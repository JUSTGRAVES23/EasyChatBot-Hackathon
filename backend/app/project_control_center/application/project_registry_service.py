from __future__ import annotations

from dataclasses import replace

from sqlalchemy.exc import IntegrityError

from ..domain.models import ProjectDefinition
from ..domain.ports import ProjectRegistry


class ProjectRegistryService:
    """Application service for authoritative Project Registry CRUD."""

    def __init__(self, registry: ProjectRegistry) -> None:
        if registry is None:
            raise ValueError("registry is required.")
        self._registry = registry

    def list_projects(self) -> list[ProjectDefinition]:
        return self._registry.list_active()

    def get_project(self, project_id: str) -> ProjectDefinition | None:
        self._validate_project_id(project_id)
        return self._registry.get(project_id)

    def create_project(
        self,
        *,
        project_id: str,
        name: str,
        description: str = "",
        owner: str | None = None,
        active: bool = True,
    ) -> ProjectDefinition:
        self._validate_project_id(project_id)
        self._validate_name(name)

        if self._registry.get(project_id) is not None:
            raise ProjectAlreadyExistsError(
                f"Project already exists: {project_id}"
            )

        project = ProjectDefinition(
            project_id=project_id,
            name=name,
            description=description,
            owner=owner,
            active=active,
        )

        try:
            return self._registry.save(project)
        except IntegrityError as exc:
            raise ProjectAlreadyExistsError(
                f"Project already exists: {project_id}"
            ) from exc

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        owner: str | None = None,
        active: bool | None = None,
    ) -> ProjectDefinition | None:
        self._validate_project_id(project_id)

        current = self._registry.get(project_id)
        if current is None:
            return None

        if name is not None:
            self._validate_name(name)

        updated = replace(
            current,
            name=current.name if name is None else name,
            description=(
                current.description
                if description is None
                else description
            ),
            owner=current.owner if owner is None else owner,
            active=current.active if active is None else active,
        )

        try:
            return self._registry.save(updated)
        except IntegrityError as exc:
            raise ProjectRegistryPersistenceError(
                f"Unable to update project: {project_id}"
            ) from exc

    @staticmethod
    def _validate_project_id(project_id: str) -> None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required.")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name is required.")


class ProjectAlreadyExistsError(ValueError):
    """Raised when a project identifier is already registered."""


class ProjectRegistryPersistenceError(RuntimeError):
    """Raised when registry persistence fails."""


__all__ = [
    "ProjectAlreadyExistsError",
    "ProjectRegistryPersistenceError",
    "ProjectRegistryService",
]
