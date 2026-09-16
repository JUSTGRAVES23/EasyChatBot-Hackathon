from __future__ import annotations

from datetime import datetime, timezone

from ..domain.models import (
    ActionSnapshot,
    ActionStatus,
    IssueSnapshot,
    IssueStatus,
    MetricSnapshot,
    MilestoneSnapshot,
    RiskSnapshot,
    Severity,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
    WorkstreamStatus,
)
from ..domain.ports import ProjectStatusSource


class DemoProjectStatusSource(ProjectStatusSource):
    """TEST/DEMO ONLY. Never use these values as production project truth."""

    @property
    def source_id(self) -> str:
        return "demo"

    @property
    def source_name(self) -> str:
        return "Demo Source"

    def health(self) -> SourceSnapshot:
        return SourceSnapshot(
            "demo", self.source_name, SourceStatus.AVAILABLE,
            datetime.now(timezone.utc)
        )

    def fetch_workstreams(self, project_id: str) -> list[WorkstreamSnapshot]:
        return [
            WorkstreamSnapshot("engineering", "Development / Engineering", 90, WorkstreamStatus.HEALTHY, "demo"),
            WorkstreamSnapshot("agents", "AI Agents", 85, WorkstreamStatus.HEALTHY, "demo"),
            WorkstreamSnapshot("quality", "Quality & Testing", 78, WorkstreamStatus.WARNING, "demo"),
            WorkstreamSnapshot("governance", "Security & Governance", 88, WorkstreamStatus.HEALTHY, "demo"),
            WorkstreamSnapshot("operations", "Provider / AI Operations", 82, WorkstreamStatus.HEALTHY, "demo"),
            WorkstreamSnapshot("beta", "Beta", 65, WorkstreamStatus.WARNING, "demo"),
        ]

    def fetch_metrics(self, project_id: str) -> list[MetricSnapshot]:
        return [
            MetricSnapshot("tests", "Tests", 955, source="demo"),
            MetricSnapshot("coverage", "Coverage", 87, "%", "demo"),
            MetricSnapshot("open_issues", "Open Issues", 12, source="demo"),
        ]

    def fetch_issues(self, project_id: str) -> list[IssueSnapshot]:
        return [
            IssueSnapshot("ISS-001", project_id, "Example quality issue", Severity.MEDIUM, IssueStatus.OPEN, "quality", "QA", "demo")
        ]

    def fetch_risks(self, project_id: str) -> list[RiskSnapshot]:
        return [
            RiskSnapshot("R-001", project_id, "Provider API rate limits", Severity.MEDIUM, "Open", "operations", "Operations", "demo"),
            RiskSnapshot("R-002", project_id, "Beta feedback volume", Severity.MEDIUM, "Monitoring", "beta", "Beta", "demo"),
        ]

    def fetch_actions(self, project_id: str) -> list[ActionSnapshot]:
        return [
            ActionSnapshot("A-001", project_id, "Refine beta test scenarios", Severity.HIGH, ActionStatus.OPEN, "Beta", "beta", source="demo"),
            ActionSnapshot("A-002", project_id, "Update M2.4 documentation", Severity.MEDIUM, ActionStatus.OPEN, "Documentation", source="demo"),
        ]

    def fetch_milestones(self, project_id: str) -> list[MilestoneSnapshot]:
        return [
            MilestoneSnapshot("M2.4", project_id, "Voice", "active", source="demo"),
            MilestoneSnapshot("M3.0", project_id, "Beta Release", "not_started", source="demo"),
        ]
