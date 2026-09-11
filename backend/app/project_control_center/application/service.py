"""
Project Control Center application service.

Composes read-only project status sources into a unified
ProjectControlSnapshot.

The service does not own authoritative project state.
Authoritative state remains in the source systems exposed
through ProjectStatusSource adapters.

Both synchronous and asynchronous composition paths are
supported:

- get_snapshot() for synchronous sources;
- get_snapshot_async() for sources that expose asynchronous
  application services.

No event-loop bridging is performed.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from ..domain.models import (
    ProjectControlSnapshot,
    ProjectDefinition,
    ProjectStatus,
    WorkstreamStatus,
)
from ..domain.ports import (
    ProjectRegistry,
    ProjectStatusSource,
    SnapshotRepository,
)


async def _maybe_await(value: Any) -> Any:
    """
    Resolve an awaitable value while preserving synchronous values.

    This helper allows the asynchronous composition path to work
    with both synchronous and asynchronous source implementations.

    It deliberately does not create or manage an event loop.
    """

    if inspect.isawaitable(value):
        return await value

    return value


@dataclass(frozen=True, slots=True)
class ProjectControlService:
    """
    Application service responsible for project-control composition.

    The service is read-oriented. It retrieves project data from
    registered ProjectStatusSource adapters and builds a unified
    ProjectControlSnapshot.

    It does not modify authoritative source systems.
    """

    registry: ProjectRegistry
    sources: tuple[ProjectStatusSource, ...]
    snapshots: SnapshotRepository

    def get_snapshot(
        self,
        project_id: str,
        *,
        persist: bool = True,
    ) -> ProjectControlSnapshot:
        """
        Build a project-control snapshot from synchronous sources.

        This method preserves the original synchronous PCD contract.

        Asynchronous sources must be consumed through
        get_snapshot_async().
        """

        project = self.registry.get(project_id)

        if project is None:
            raise ValueError(
                f"Unknown project: {project_id}"
            )

        workstreams = []
        metrics = []
        issues = []
        risks = []
        actions = []
        milestones = []
        source_health = []

        for source in self.sources:
            source_health.append(source.health())

            workstreams.extend(
                source.fetch_workstreams(project_id)
            )
            metrics.extend(
                source.fetch_metrics(project_id)
            )
            issues.extend(
                source.fetch_issues(project_id)
            )
            risks.extend(
                source.fetch_risks(project_id)
            )
            actions.extend(
                source.fetch_actions(project_id)
            )
            milestones.extend(
                source.fetch_milestones(project_id)
            )

        snapshot = self._build_snapshot(
            project=project,
            workstreams=workstreams,
            metrics=metrics,
            issues=issues,
            risks=risks,
            actions=actions,
            milestones=milestones,
            source_health=source_health,
        )

        if persist:
            self.snapshots.save(snapshot)

        return snapshot

    async def get_snapshot_async(
        self,
        project_id: str,
        *,
        persist: bool = True,
    ) -> ProjectControlSnapshot:
        """
        Build a project-control snapshot from sync/async sources.

        This is the production composition path for PCD adapters
        backed by asynchronous application services.

        The method awaits asynchronous source operations directly.
        It does not call asyncio.run(), create a nested event loop,
        or otherwise bridge asynchronous execution into synchronous
        code.
        """

        project = self.registry.get(project_id)

        if project is None:
            raise ValueError(
                f"Unknown project: {project_id}"
            )

        workstreams = []
        metrics = []
        issues = []
        risks = []
        actions = []
        milestones = []
        source_health = []

        for source in self.sources:
            source_health.append(source.health())

            workstreams.extend(
                await _maybe_await(
                    source.fetch_workstreams(project_id)
                )
            )
            metrics.extend(
                await _maybe_await(
                    source.fetch_metrics(project_id)
                )
            )
            issues.extend(
                await _maybe_await(
                    source.fetch_issues(project_id)
                )
            )
            risks.extend(
                await _maybe_await(
                    source.fetch_risks(project_id)
                )
            )
            actions.extend(
                await _maybe_await(
                    source.fetch_actions(project_id)
                )
            )
            milestones.extend(
                await _maybe_await(
                    source.fetch_milestones(project_id)
                )
            )

        snapshot = self._build_snapshot(
            project=project,
            workstreams=workstreams,
            metrics=metrics,
            issues=issues,
            risks=risks,
            actions=actions,
            milestones=milestones,
            source_health=source_health,
        )

        if persist:
            self.snapshots.save(snapshot)

        return snapshot

    @staticmethod
    def _build_snapshot(
        *,
        project: ProjectDefinition,
        workstreams: list,
        metrics: list,
        issues: list,
        risks: list,
        actions: list,
        milestones: list,
        source_health: list,
    ) -> ProjectControlSnapshot:
        """
        Deterministically compose the unified project snapshot.

        No source is mutated and no new authoritative state is
        created here.
        """

        progress_values = [
            workstream.completion_percent
            for workstream in workstreams
            if workstream.completion_percent is not None
        ]

        progress = (
            round(
                sum(progress_values) / len(progress_values),
                1,
            )
            if progress_values
            else None
        )

        blockers = (
            sum(
                1
                for workstream in workstreams
                if workstream.status is WorkstreamStatus.BLOCKED
            )
            + sum(
                1
                for issue in issues
                if issue.status.value in {
                    "open",
                    "in_progress",
                }
                and issue.severity.value in {
                    "high",
                    "critical",
                }
            )
        )

        open_risks = sum(
            1
            for risk in risks
            if risk.status.lower()
            not in {
                "closed",
                "resolved",
            }
        )

        warnings = sum(
            1
            for workstream in workstreams
            if workstream.status is WorkstreamStatus.WARNING
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
            (
                milestone.name
                for milestone in milestones
                if milestone.status.lower()
                in {
                    "active",
                    "in_progress",
                }
            ),
            None,
        )

        current_workstream = next(
            (
                workstream.name
                for workstream in workstreams
                if workstream.status
                in {
                    WorkstreamStatus.WARNING,
                    WorkstreamStatus.BLOCKED,
                }
            ),
            None,
        )

        return ProjectControlSnapshot(
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

    def list_projects(self) -> list[ProjectDefinition]:
        """Return active projects from the authoritative registry."""

        return self.registry.list_active()