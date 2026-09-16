from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import ProjectControlSnapshot
from .service import ProjectControlService


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    projects: tuple[ProjectControlSnapshot, ...]
    generated_at: str


class PortfolioControlService:
    """Phase 2/3 portfolio read model built from project snapshots."""

    def __init__(self, project_control: ProjectControlService) -> None:
        self._project_control = project_control

    def get_portfolio(self) -> PortfolioSnapshot:
        snapshots = tuple(
            self._project_control.get_snapshot(project.project_id)
            for project in self._project_control.list_projects()
        )
        generated_at = (
            max((s.generated_at for s in snapshots), default=None)
        )
        return PortfolioSnapshot(
            projects=snapshots,
            generated_at=generated_at.isoformat() if generated_at else "",
        )
