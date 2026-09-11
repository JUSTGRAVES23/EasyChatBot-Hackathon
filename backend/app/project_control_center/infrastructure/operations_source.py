from __future__ import annotations

from datetime import datetime, timezone

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.operational_incident import (
    IncidentStatus,
)

from ..domain.models import (
    ActionSnapshot,
    IssueSnapshot,
    IssueStatus,
    MetricSnapshot,
    MilestoneSnapshot,
    RiskSnapshot,
    Severity,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
)
from ..domain.ports import ProjectStatusSource


class OperationsProjectStatusSource(ProjectStatusSource):
    """Read-only PCD adapter over the existing Operations Center state.

    OperationalDashboardService remains the application-owned Operations
    boundary. This adapter does not create another incident store and does
    not access infrastructure directly.

    PCD-2B integrates operational incidents as dashboard issues because
    incidents represent actionable operational problems. It deliberately
    does not invent project workstreams, risks, actions, or milestones
    where the Operations Center has no authoritative contract for them.
    """

    _SOURCE_ID = "operations-center"
    _SOURCE_NAME = "Operations Center"

    def __init__(
        self,
        *,
        dashboard_service: OperationalDashboardService,
    ) -> None:
        if dashboard_service is None:
            raise ValueError(
                "dashboard_service cannot be None."
            )

        self._dashboard_service = dashboard_service

    @property
    def source_id(self) -> str:
        return self._SOURCE_ID

    @property
    def source_name(self) -> str:
        return self._SOURCE_NAME

    def health(self) -> SourceSnapshot:
        """Report adapter availability without performing a new probe.

        The Operations dashboard itself owns fresh health evaluation.
        ProjectStatusSource.health() is synchronous, so this method does
        not attempt to bridge into the asynchronous dashboard service.
        """
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    async def fetch_dashboard(
        self,
    ):
        """Return the authoritative Operations dashboard snapshot."""
        return await (
            self._dashboard_service
            .create_dashboard_snapshot()
        )

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        """Operations Center does not own project workstreams."""
        return []

    async def fetch_metrics(
        self,
        project_id: str,
    ) -> list[MetricSnapshot]:
        """Translate authoritative operational metrics into PCD metrics."""
        dashboard = await self.fetch_dashboard()

        return [
            MetricSnapshot(
                key="operations.open_incidents",
                label="Open Operational Incidents",
                value=dashboard.private_classroom.incidents.open
                + dashboard.announcement_group.incidents.open,
                source=self.source_id,
                observed_at=dashboard.generated_at,
            ),
            MetricSnapshot(
                key="operations.critical_incidents",
                label="Critical Operational Incidents",
                value=dashboard.private_classroom.incidents.critical
                + dashboard.announcement_group.incidents.critical,
                source=self.source_id,
                observed_at=dashboard.generated_at,
            ),
            MetricSnapshot(
                key="operations.message_failures",
                label="Operational Message Failures",
                value=(
                    dashboard.private_classroom.metrics.message_failures
                    + dashboard.announcement_group.metrics.message_failures
                ),
                source=self.source_id,
                observed_at=dashboard.generated_at,
            ),
            MetricSnapshot(
                key="operations.rate_limit_events",
                label="Rate Limit Events",
                value=(
                    dashboard.private_classroom.metrics.rate_limit_events
                    + dashboard.announcement_group.metrics.rate_limit_events
                ),
                source=self.source_id,
                observed_at=dashboard.generated_at,
            ),
            MetricSnapshot(
                key="operations.abuse_events",
                label="Abuse Events",
                value=(
                    dashboard.private_classroom.metrics.abuse_events
                    + dashboard.announcement_group.metrics.abuse_events
                ),
                source=self.source_id,
                observed_at=dashboard.generated_at,
            ),
        ]

    async def fetch_issues(
        self,
        project_id: str,
    ) -> list[IssueSnapshot]:
        """Translate current operational incidents into PCD issues.

        Incident content/events are intentionally not copied into the PCD
        issue model. Only dashboard-safe operational identifiers and state
        are exposed.
        """
        dashboard = await self.fetch_dashboard()

        issues: list[IssueSnapshot] = []

        for incident in dashboard.incidents:
            issues.append(
                IssueSnapshot(
                    issue_id=incident.incident_id,
                    project_id=project_id,
                    title=(
                        f"Operational incident "
                        f"{incident.incident_id}"
                    ),
                    severity=self._map_severity(
                        incident.severity
                    ),
                    status=self._map_issue_status(
                        incident.status
                    ),
                    owner=None,
                    source=self.source_id,
                )
            )

        return issues

    def fetch_risks(
        self,
        project_id: str,
    ) -> list[RiskSnapshot]:
        """Operations Center does not own project risks."""
        return []

    def fetch_actions(
        self,
        project_id: str,
    ) -> list[ActionSnapshot]:
        """Operations Center does not own project actions."""
        return []

    def fetch_milestones(
        self,
        project_id: str,
    ) -> list[MilestoneSnapshot]:
        """Operations Center does not own project milestones."""
        return []

    @staticmethod
    def _map_severity(
        severity: str,
    ) -> Severity:
        try:
            return Severity(severity.lower())
        except ValueError:
            return Severity.MEDIUM

    @staticmethod
    def _map_issue_status(
        status: str,
    ) -> IssueStatus:
        normalized = status.lower()

        if normalized in {
            IncidentStatus.RESOLVED.value,
            IncidentStatus.CLOSED.value,
        }:
            return IssueStatus.RESOLVED

        if normalized in {
            IncidentStatus.INVESTIGATING.value,
            IncidentStatus.ACKNOWLEDGED.value,
            IncidentStatus.OPEN.value,
            IncidentStatus.DETECTED.value,
        }:
            return IssueStatus.IN_PROGRESS

        return IssueStatus.OPEN


__all__ = [
    "OperationsProjectStatusSource",
]
