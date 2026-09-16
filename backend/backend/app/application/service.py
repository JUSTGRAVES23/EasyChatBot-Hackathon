from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import (
    ProjectControlSnapshot,
    ProjectStatus,
    ProjectDefinition,
    WorkstreamStatus,
)
from ..domain.ports import ProjectRegistry, ProjectStatusSource, SnapshotRepository


@dataclass(frozen=True, slots=True)
class ProjectControlService:
    registry: ProjectRegistry
    sources: tuple[ProjectStatusSource, ...]
    snapshots: SnapshotRepository

    def get_snapshot(self, project_id: str, *, persist: bool = True) -> ProjectControlSnapshot:
        project = self.registry.get(project_id)
        if project is None:
            raise ValueError(f"Unknown project: {project_id}")

        workstreams = []
        metrics = []
        issues = []
        risks = []
        actions = []
        milestones = []
        source_health = []

        for source in self.sources:
            source_health.append(source.health())
            workstreams.extend(source.fetch_workstreams(project_id))
            metrics.extend(source.fetch_metrics(project_id))
            issues.extend(source.fetch_issues(project_id))
            risks.extend(source.fetch_risks(project_id))
            actions.extend(source.fetch_actions(project_id))
            milestones.extend(source.fetch_milestones(project_id))

        progress_values = [
            w.completion_percent for w in workstreams
            if w.completion_percent is not None
        ]
        progress = (
            round(sum(progress_values) / len(progress_values), 1)
            if progress_values else None
        )

        blockers = (
            sum(1 for w in workstreams if w.status is WorkstreamStatus.BLOCKED)
            + sum(
                1 for i in issues
                if i.status.value in {"open", "in_progress"}
                and i.severity.value in {"high", "critical"}
            )
        )

        open_risks = sum(
            1 for risk in risks
            if risk.status.lower() not in {"closed", "resolved"}
        )

        warnings = sum(
            1 for w in workstreams if w.status is WorkstreamStatus.WARNING
        )

        if blockers:
            status = ProjectStatus.BLOCKED
        elif progress is not None and progress >= 100:
            status = ProjectStatus.COMPLETE
        elif warnings or open_risks:
            status = ProjectStatus.AT_RISK
        elif workstreams:
            status = ProjectStatus.ON_TRACK
        else:
            status = ProjectStatus.UNKNOWN

        if blockers:
            readiness = "NOT READY"
        elif progress is not None and progress >= 80:
            readiness = "BETA READY"
        elif progress is not None:
            readiness = "IN PROGRESS"
        else:
            readiness = "UNKNOWN"

        current_milestone = next(
            (m.name for m in milestones if m.status.lower() in {"active", "in_progress"}),
            None,
        )
        current_workstream = next(
            (
                w.name for w in workstreams
                if w.status in {WorkstreamStatus.WARNING, WorkstreamStatus.BLOCKED}
            ),
            None,
        )

        snapshot = ProjectControlSnapshot(
            project_id=project.project_id,
            project_name=project.name,
            project_status=status,
            overall_progress_percent=progress,
            current_milestone=current_milestone,
            current_workstream=current_workstream,
            release_readiness=readiness,
            open_blockers=blockers,
            open_risks=open_risks,
            workstreams=tuple(workstreams),
            metrics=tuple(metrics),
            issues=tuple(issues),
            risks=tuple(risks),
            actions=tuple(actions),
            milestones=tuple(milestones),
            sources=tuple(source_health),
        )
        if persist:
            self.snapshots.save(snapshot)
        return snapshot

    def list_projects(self) -> list[ProjectDefinition]:
        return self.registry.list_active()
