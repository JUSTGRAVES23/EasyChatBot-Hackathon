from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.application.health.health_result import HealthStatus
from app.application.health.operational_dashboard_models import (
    DashboardIncident,
    DashboardIncidentSummary,
    DashboardOperationalMetrics,
    DashboardSurfaceStatus,
    OperationalDashboardSnapshot,
)
from app.application.health.operational_event import (
    OperationalSurface,
)
from app.project_control_center.domain.models import (
    IssueStatus,
    Severity,
    SourceStatus,
)
from app.project_control_center.infrastructure.operations_source import (
    OperationsProjectStatusSource,
)


@dataclass
class FakeDashboardService:
    snapshot: OperationalDashboardSnapshot
    calls: int = 0

    async def create_dashboard_snapshot(
        self,
    ) -> OperationalDashboardSnapshot:
        self.calls += 1
        return self.snapshot


def make_dashboard(
    *,
    incidents: tuple[DashboardIncident, ...] = (),
) -> OperationalDashboardSnapshot:
    generated_at = datetime.now(timezone.utc)

    empty_surface = DashboardSurfaceStatus(
        surface=OperationalSurface.PRIVATE_CLASSROOM,
        status=HealthStatus.HEALTHY,
        incidents=DashboardIncidentSummary(),
        metrics=DashboardOperationalMetrics(),
    )

    empty_announcement = DashboardSurfaceStatus(
        surface=OperationalSurface.ANNOUNCEMENT_GROUP,
        status=HealthStatus.HEALTHY,
        incidents=DashboardIncidentSummary(),
        metrics=DashboardOperationalMetrics(),
    )

    return OperationalDashboardSnapshot(
        generated_at=generated_at,
        overall_status=HealthStatus.HEALTHY,
        health_score=100,
        private_classroom=empty_surface,
        announcement_group=empty_announcement,
        incidents=incidents,
    )


def make_incident(
    *,
    incident_id: str = "incident-001",
    severity: str = "high",
    status: str = "open",
) -> DashboardIncident:
    now = datetime.now(timezone.utc)

    return DashboardIncident(
        incident_id=incident_id,
        correlation_id=f"corr-{incident_id}",
        surface=OperationalSurface.PRIVATE_CLASSROOM,
        severity=severity,
        status=status,
        first_seen=now,
        last_seen=now,
        occurrence_count=1,
    )


def test_none_dashboard_service_is_rejected():
    with pytest.raises(
        ValueError,
        match="dashboard_service cannot be None",
    ):
        OperationsProjectStatusSource(
            dashboard_service=None,
        )


def test_health_does_not_probe_operations_service():
    service = FakeDashboardService(
        snapshot=make_dashboard(),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    result = source.health()

    assert result.source_id == "operations-center"
    assert result.name == "Operations Center"
    assert result.status is SourceStatus.AVAILABLE
    assert service.calls == 0


@pytest.mark.asyncio
async def test_fetch_dashboard_uses_authoritative_dashboard_service():
    service = FakeDashboardService(
        snapshot=make_dashboard(),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    result = await source.fetch_dashboard()

    assert result.overall_status is HealthStatus.HEALTHY
    assert service.calls == 1


@pytest.mark.asyncio
async def test_operational_incident_becomes_pcd_issue():
    incident = make_incident(
        incident_id="incident-high",
        severity="high",
        status="open",
    )

    service = FakeDashboardService(
        snapshot=make_dashboard(
            incidents=(incident,),
        ),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    issues = await source.fetch_issues(
        "easychatbot",
    )

    assert len(issues) == 1

    issue = issues[0]

    assert issue.issue_id == "incident-high"
    assert issue.project_id == "easychatbot"
    assert issue.severity is Severity.HIGH
    assert issue.status is IssueStatus.IN_PROGRESS
    assert issue.source == "operations-center"
    assert issue.owner is None


@pytest.mark.asyncio
async def test_resolved_incident_becomes_resolved_issue():
    incident = make_incident(
        incident_id="incident-resolved",
        severity="medium",
        status="resolved",
    )

    service = FakeDashboardService(
        snapshot=make_dashboard(
            incidents=(incident,),
        ),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    issues = await source.fetch_issues(
        "easychatbot",
    )

    assert issues[0].status is IssueStatus.RESOLVED


@pytest.mark.asyncio
async def test_unknown_incident_severity_is_safe():
    incident = make_incident(
        incident_id="incident-unknown",
        severity="unexpected",
        status="open",
    )

    service = FakeDashboardService(
        snapshot=make_dashboard(
            incidents=(incident,),
        ),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    issues = await source.fetch_issues(
        "easychatbot",
    )

    assert issues[0].severity is Severity.MEDIUM


@pytest.mark.asyncio
async def test_operations_does_not_invent_project_entities():
    service = FakeDashboardService(
        snapshot=make_dashboard(),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    assert source.fetch_workstreams(
        "easychatbot"
    ) == []

    assert source.fetch_risks(
        "easychatbot"
    ) == []

    assert source.fetch_actions(
        "easychatbot"
    ) == []

    assert source.fetch_milestones(
        "easychatbot"
    ) == []


@pytest.mark.asyncio
async def test_operational_metrics_are_translated_without_event_content():
    generated_at = datetime.now(timezone.utc)

    private = DashboardSurfaceStatus(
        surface=OperationalSurface.PRIVATE_CLASSROOM,
        status=HealthStatus.HEALTHY,
        incidents=DashboardIncidentSummary(
            open=2,
            critical=1,
        ),
        metrics=DashboardOperationalMetrics(
            message_failures=3,
            rate_limit_events=4,
            abuse_events=5,
        ),
    )

    announcement = DashboardSurfaceStatus(
        surface=OperationalSurface.ANNOUNCEMENT_GROUP,
        status=HealthStatus.HEALTHY,
        incidents=DashboardIncidentSummary(
            open=1,
            critical=1,
        ),
        metrics=DashboardOperationalMetrics(
            message_failures=6,
            rate_limit_events=7,
            abuse_events=8,
        ),
    )

    dashboard = OperationalDashboardSnapshot(
        generated_at=generated_at,
        overall_status=HealthStatus.HEALTHY,
        health_score=100,
        private_classroom=private,
        announcement_group=announcement,
    )

    service = FakeDashboardService(
        snapshot=dashboard,
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    metrics = await source.fetch_metrics(
        "easychatbot",
    )

    values = {
        metric.key: metric.value
        for metric in metrics
    }

    assert values["operations.open_incidents"] == 3
    assert values["operations.critical_incidents"] == 2
    assert values["operations.message_failures"] == 9
    assert values["operations.rate_limit_events"] == 11
    assert values["operations.abuse_events"] == 13

    serialized = str(metrics).lower()

    assert "message content" not in serialized
    assert "password" not in serialized
    assert "api_key" not in serialized


@pytest.mark.asyncio
async def test_multiple_incidents_are_preserved_as_separate_issues():
    incidents = (
        make_incident(
            incident_id="incident-001",
            severity="critical",
            status="open",
        ),
        make_incident(
            incident_id="incident-002",
            severity="low",
            status="acknowledged",
        ),
    )

    service = FakeDashboardService(
        snapshot=make_dashboard(
            incidents=incidents,
        ),
    )

    source = OperationsProjectStatusSource(
        dashboard_service=service,
    )

    issues = await source.fetch_issues(
        "easychatbot",
    )

    assert [issue.issue_id for issue in issues] == [
        "incident-001",
        "incident-002",
    ]

    assert issues[0].severity is Severity.CRITICAL
    assert issues[1].severity is Severity.LOW
    assert all(
        issue.project_id == "easychatbot"
        for issue in issues
    )
