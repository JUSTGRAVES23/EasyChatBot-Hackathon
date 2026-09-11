from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.project_control_center.application.service import (
    ProjectControlService,
)
from app.project_control_center.domain.models import (
    ActionSnapshot,
    ActionStatus,
    IssueSnapshot,
    IssueStatus,
    MetricSnapshot,
    MilestoneSnapshot,
    ProjectDefinition,
    RiskSnapshot,
    Severity,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
    WorkstreamStatus,
)
from app.project_control_center.domain.ports import ProjectStatusSource
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)


@dataclass
class MixedSource(ProjectStatusSource):
    """
    Test source supporting both synchronous and asynchronous
    source methods.

    This represents the compatibility requirement of the
    asynchronous composition path.
    """

    @property
    def source_id(self) -> str:
        return "mixed"

    @property
    def source_name(self) -> str:
        return "Mixed Source"

    def health(self) -> SourceSnapshot:
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        return [
            WorkstreamSnapshot(
                workstream_id="engineering",
                name="Engineering",
                completion_percent=90,
                status=WorkstreamStatus.HEALTHY,
                source=self.source_id,
            )
        ]

    async def fetch_metrics(
        self,
        project_id: str,
    ) -> list[MetricSnapshot]:
        return [
            MetricSnapshot(
                key="tests",
                label="Tests",
                value=955,
                source=self.source_id,
            )
        ]

    async def fetch_issues(
        self,
        project_id: str,
    ) -> list[IssueSnapshot]:
        return [
            IssueSnapshot(
                issue_id="ISS-1",
                project_id=project_id,
                title="High severity issue",
                severity=Severity.HIGH,
                status=IssueStatus.OPEN,
                source=self.source_id,
            )
        ]

    async def fetch_risks(
        self,
        project_id: str,
    ) -> list[RiskSnapshot]:
        return [
            RiskSnapshot(
                risk_id="RISK-1",
                project_id=project_id,
                title="Governance risk",
                severity=Severity.HIGH,
                status="PENDING_DPO_GRC",
                source=self.source_id,
            )
        ]

    def fetch_actions(
        self,
        project_id: str,
    ) -> list[ActionSnapshot]:
        return []

    def fetch_milestones(
        self,
        project_id: str,
    ) -> list[MilestoneSnapshot]:
        return []


class SyncSource(ProjectStatusSource):
    """
    Fully synchronous source used to verify that the existing
    synchronous composition path remains intact.
    """

    @property
    def source_id(self) -> str:
        return "sync-test"

    @property
    def source_name(self) -> str:
        return "Synchronous Test Source"

    def health(self) -> SourceSnapshot:
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        return [
            WorkstreamSnapshot(
                workstream_id="engineering",
                name="Engineering",
                completion_percent=90,
                status=WorkstreamStatus.HEALTHY,
                source=self.source_id,
            )
        ]

    def fetch_metrics(
        self,
        project_id: str,
    ) -> list[MetricSnapshot]:
        return [
            MetricSnapshot(
                key="tests",
                label="Tests",
                value=955,
                source=self.source_id,
            )
        ]

    def fetch_issues(
        self,
        project_id: str,
    ) -> list[IssueSnapshot]:
        return []

    def fetch_risks(
        self,
        project_id: str,
    ) -> list[RiskSnapshot]:
        return []

    def fetch_actions(
        self,
        project_id: str,
    ) -> list[ActionSnapshot]:
        return []

    def fetch_milestones(
        self,
        project_id: str,
    ) -> list[MilestoneSnapshot]:
        return []


def make_service(
    source: ProjectStatusSource,
) -> ProjectControlService:
    registry = InMemoryProjectRegistry()
    snapshots = InMemorySnapshotRepository()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
        )
    )

    return ProjectControlService(
        registry=registry,
        sources=(source,),
        snapshots=snapshots,
    )


@pytest.mark.asyncio
async def test_async_composition_builds_snapshot():
    service = make_service(MixedSource())

    snapshot = await service.get_snapshot_async(
        "easychatbot",
        persist=False,
    )

    assert snapshot.project_id == "easychatbot"
    assert snapshot.project_name == "EasyChatBot"


@pytest.mark.asyncio
async def test_async_composition_aggregates_all_source_data():
    service = make_service(MixedSource())

    snapshot = await service.get_snapshot_async(
        "easychatbot",
        persist=False,
    )

    assert len(snapshot.workstreams) == 1
    assert len(snapshot.metrics) == 1
    assert len(snapshot.issues) == 1
    assert len(snapshot.risks) == 1


@pytest.mark.asyncio
async def test_async_composition_preserves_existing_status_rules():
    service = make_service(MixedSource())

    snapshot = await service.get_snapshot_async(
        "easychatbot",
        persist=False,
    )

    assert snapshot.project_status.value == "blocked"
    assert snapshot.open_blockers == 1
    assert snapshot.open_risks == 1
    assert snapshot.release_readiness == "NOT READY"


@pytest.mark.asyncio
async def test_async_composition_persists_snapshot():
    service = make_service(MixedSource())

    snapshot = await service.get_snapshot_async(
        "easychatbot",
    )

    stored = service.snapshots.list_for_project(
        "easychatbot"
    )

    assert stored
    assert stored[-1] == snapshot


@pytest.mark.asyncio
async def test_unknown_project_is_rejected():
    service = make_service(MixedSource())

    with pytest.raises(
        ValueError,
        match="Unknown project: missing",
    ):
        await service.get_snapshot_async(
            "missing",
            persist=False,
        )


def test_existing_sync_composition_remains_unchanged():
    service = make_service(SyncSource())

    snapshot = service.get_snapshot(
        "easychatbot",
        persist=False,
    )

    assert snapshot.project_id == "easychatbot"
    assert snapshot.project_name == "EasyChatBot"
    assert snapshot.overall_progress_percent == 90
    assert snapshot.project_status.value == "on_track"