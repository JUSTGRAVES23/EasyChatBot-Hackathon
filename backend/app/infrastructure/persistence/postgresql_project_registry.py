from __future__ import annotations

from sqlalchemy import select

from app.project_control_center.domain.models import ProjectDefinition
from app.project_control_center.domain.ports import (
    ProjectRegistry,
    ProjectRegistryBulkWriter,
)

from .project_registry_records import ProjectRegistryRecord


class PostgreSQLProjectRegistry(ProjectRegistry, ProjectRegistryBulkWriter):
    """PostgreSQL implementation of the authoritative Project Registry."""

    def __init__(self, session_factory) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")

        self._session_factory = session_factory

    def get(self, project_id: str) -> ProjectDefinition | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(ProjectRegistryRecord).where(
                    ProjectRegistryRecord.project_id == project_id,
                )
            )

        if record is None:
            return None

        return self._to_domain(record)

    def list_active(self) -> list[ProjectDefinition]:
        with self._session_factory() as session:
            records = session.scalars(
                select(ProjectRegistryRecord)
                .where(ProjectRegistryRecord.active.is_(True))
                .order_by(
                    ProjectRegistryRecord.name.asc(),
                    ProjectRegistryRecord.project_id.asc(),
                )
            ).all()

        return [self._to_domain(record) for record in records]

    def save(self, project: ProjectDefinition) -> ProjectDefinition:
        if project is None:
            raise ValueError("project is required.")

        with self._session_factory() as session:
            record = session.get(
                ProjectRegistryRecord,
                project.project_id,
            )

            if record is None:
                record = ProjectRegistryRecord(
                    project_id=project.project_id,
                    name=project.name,
                    description=project.description,
                    owner=project.owner,
                    active=project.active,
                    created_at=project.created_at,
                )
                session.add(record)
            else:
                record.name = project.name
                record.description = project.description
                record.owner = project.owner
                record.active = project.active

            session.commit()

        return project

    def create_many(
        self,
        projects: list[ProjectDefinition],
    ) -> list[ProjectDefinition]:
        return self._persist_many(projects, overwrite=False)

    def upsert_many(
        self,
        projects: list[ProjectDefinition],
    ) -> list[ProjectDefinition]:
        return self._persist_many(projects, overwrite=True)

    def _persist_many(
        self,
        projects: list[ProjectDefinition],
        *,
        overwrite: bool,
    ) -> list[ProjectDefinition]:
        if not projects:
            raise ValueError("projects are required.")

        with self._session_factory() as session:
            for project in projects:
                record = session.get(
                    ProjectRegistryRecord,
                    project.project_id,
                )
                if record is None:
                    session.add(
                        ProjectRegistryRecord(
                            project_id=project.project_id,
                            name=project.name,
                            description=project.description,
                            owner=project.owner,
                            active=project.active,
                            created_at=project.created_at,
                        )
                    )
                elif overwrite:
                    record.name = project.name
                    record.description = project.description
                    record.owner = project.owner
                    record.active = project.active
                else:
                    raise ValueError(
                        f"Project already exists: {project.project_id}"
                    )

            session.commit()

        return projects

    @staticmethod
    def _to_domain(
        record: ProjectRegistryRecord,
    ) -> ProjectDefinition:
        return ProjectDefinition(
            project_id=record.project_id,
            name=record.name,
            description=record.description,
            owner=record.owner,
            active=record.active,
            created_at=record.created_at,
        )


__all__ = ["PostgreSQLProjectRegistry"]
