from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..domain.models import ProjectEvent, ProjectEventType
from ..domain.ports import ProjectEventRepository


class ProjectEventService:
    """Records project-control events; it does not mutate source systems."""

    def __init__(self, repository: ProjectEventRepository) -> None:
        self._repository = repository

    def record(
        self,
        *,
        project_id: str,
        event_type: ProjectEventType,
        summary: str,
        source: str,
        metadata: dict[str, str] | None = None,
    ) -> ProjectEvent:
        event = ProjectEvent(
            event_id=f"pev-{uuid4()}",
            project_id=project_id,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            summary=summary,
            source=source,
            metadata=tuple(sorted((metadata or {}).items())),
        )
        return self._repository.save(event)
