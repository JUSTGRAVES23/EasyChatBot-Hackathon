from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import ProjectControlSnapshot
from ..domain.ports import SnapshotRepository


@dataclass(frozen=True, slots=True)
class ProjectTrend:
    project_id: str
    snapshots: tuple[ProjectControlSnapshot, ...]
    progress_delta: float | None
    blocker_delta: int | None
    risk_delta: int | None


class ProjectHistoryService:
    def __init__(self, repository: SnapshotRepository) -> None:
        self._repository = repository

    def trend(self, project_id: str, limit: int = 30) -> ProjectTrend:
        snapshots = tuple(self._repository.list_for_project(project_id, limit))
        if len(snapshots) < 2:
            return ProjectTrend(project_id, snapshots, None, None, None)

        latest, previous = snapshots[0], snapshots[1]

        progress_delta = None
        if (
            latest.overall_progress_percent is not None
            and previous.overall_progress_percent is not None
        ):
            progress_delta = round(
                latest.overall_progress_percent
                - previous.overall_progress_percent,
                1,
            )

        return ProjectTrend(
            project_id=project_id,
            snapshots=snapshots,
            progress_delta=progress_delta,
            blocker_delta=latest.open_blockers - previous.open_blockers,
            risk_delta=latest.open_risks - previous.open_risks,
        )
